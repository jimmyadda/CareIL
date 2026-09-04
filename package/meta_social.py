import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from cryptography.fernet import Fernet, InvalidToken


SCOPES = ('pages_show_list', 'pages_read_engagement', 'pages_manage_posts')


class MetaSocialError(RuntimeError):
    pass


def graph_version():
    return os.environ.get('META_GRAPH_API_VERSION', 'v24.0').strip() or 'v24.0'


def is_configured():
    return bool(os.environ.get('META_APP_ID') and os.environ.get('META_APP_SECRET'))


def authorization_url(redirect_uri, state):
    if not is_configured():
        raise MetaSocialError('Meta credentials are not configured.')
    query = urllib.parse.urlencode({
        'client_id': os.environ['META_APP_ID'],
        'redirect_uri': redirect_uri,
        'state': state,
        'response_type': 'code',
        'scope': ','.join(SCOPES),
    })
    return f'https://www.facebook.com/{graph_version()}/dialog/oauth?{query}'


def _fernet():
    secret = os.environ.get('THERAPY_SECRET_KEY', 'change-this-development-key').encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _encrypt(value):
    return _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def _decrypt(value):
    try:
        return _fernet().decrypt(value.encode('ascii')).decode('utf-8')
    except InvalidToken as error:
        raise MetaSocialError(
            'The saved Meta token cannot be decrypted. Check THERAPY_SECRET_KEY.'
        ) from error


def _graph_url(path):
    return f'https://graph.facebook.com/{graph_version()}/{path.lstrip("/")}'


def _request_json(path, method='GET', params=None, access_token=None, timeout=25):
    values = dict(params or {})
    if access_token:
        values['access_token'] = access_token
        app_secret = os.environ.get('META_APP_SECRET', '')
        if app_secret:
            values['appsecret_proof'] = hmac.new(
                app_secret.encode('utf-8'), access_token.encode('utf-8'), hashlib.sha256
            ).hexdigest()
    encoded = urllib.parse.urlencode(values).encode('utf-8')
    url = _graph_url(path)
    body = encoded if method == 'POST' else None
    if method == 'GET' and encoded:
        url += '?' + encoded.decode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(raw)
            detail = payload.get('error', {})
            message = detail.get('message') or raw
        except (ValueError, AttributeError):
            message = raw
        raise MetaSocialError(f'Meta API returned {error.code}: {message}') from error
    except urllib.error.URLError as error:
        raise MetaSocialError(f'Could not reach Meta: {error.reason}') from error


def exchange_code_and_find_page(code, redirect_uri):
    token_result = _request_json('oauth/access_token', params={
        'client_id': os.environ['META_APP_ID'],
        'client_secret': os.environ['META_APP_SECRET'],
        'redirect_uri': redirect_uri,
        'code': code,
    })
    short_token = token_result.get('access_token')
    if not short_token:
        raise MetaSocialError('Meta did not return a user access token.')
    long_result = _request_json('oauth/access_token', params={
        'grant_type': 'fb_exchange_token',
        'client_id': os.environ['META_APP_ID'],
        'client_secret': os.environ['META_APP_SECRET'],
        'fb_exchange_token': short_token,
    })
    user_token = long_result.get('access_token') or short_token
    pages = _request_json(
        'me/accounts',
        params={'fields': 'id,name,access_token,tasks', 'limit': 100},
        access_token=user_token,
    ).get('data', [])
    required_page_id = os.environ.get('META_PAGE_ID', '').strip()
    if required_page_id:
        matches = [page for page in pages if str(page.get('id')) == required_page_id]
    else:
        matches = [page for page in pages if str(page.get('name', '')).lower() == 'careil']
        if not matches and len(pages) == 1:
            matches = pages
    if not matches:
        raise MetaSocialError(
            'CareIL Page was not available to this Meta account. Set META_PAGE_ID if the account manages multiple Pages.'
        )
    page = matches[0]
    if not page.get('access_token'):
        raise MetaSocialError('Meta did not return a Page access token.')
    return page


def save_connection(conn, page, connected_by):
    conn.execute('''
        INSERT INTO meta_social_connections
            (connection_id, page_id, page_name, page_access_token_encrypted,
             connected_by, granted_scopes)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(connection_id) DO UPDATE SET
            page_id=excluded.page_id,
            page_name=excluded.page_name,
            page_access_token_encrypted=excluded.page_access_token_encrypted,
            connected_by=excluded.connected_by,
            granted_scopes=excluded.granted_scopes,
            updated_at=CURRENT_TIMESTAMP
    ''', (
        str(page['id']), page.get('name', 'CareIL'), _encrypt(page['access_token']),
        connected_by, ','.join(SCOPES),
    ))
    conn.commit()


def connection_status(conn):
    return conn.execute('''
        SELECT page_id, page_name, connected_by, granted_scopes, connected_at, updated_at
        FROM meta_social_connections WHERE connection_id=1
    ''').fetchone()


def disconnect(conn):
    conn.execute('DELETE FROM meta_social_connections WHERE connection_id=1')
    conn.commit()


def create_draft(conn, message, image_url, created_by):
    message = str(message or '').strip()
    image_url = str(image_url or '').strip() or None
    if not message:
        raise MetaSocialError('Post text is required.')
    if len(message) > 60000:
        raise MetaSocialError('Post text is too long.')
    if image_url:
        parsed = urllib.parse.urlparse(image_url)
        if parsed.scheme != 'https' or not parsed.netloc:
            raise MetaSocialError('Image URL must be a public HTTPS URL.')
    cursor = conn.execute('''
        INSERT INTO social_post_drafts (message, image_url, created_by)
        VALUES (?, ?, ?)
    ''', (message, image_url, created_by))
    conn.commit()
    return cursor.lastrowid


def list_drafts(conn, limit=30):
    return conn.execute('''
        SELECT * FROM social_post_drafts ORDER BY created_at DESC LIMIT ?
    ''', (limit,)).fetchall()


def approve_draft(conn, draft_id, approved_by, approval_reference):
    result = conn.execute('''
        UPDATE social_post_drafts
        SET status='approved', approved_by=?, approval_reference=?,
            approved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP,
            error_message=NULL
        WHERE draft_id=? AND status IN ('draft', 'failed')
    ''', (approved_by, approval_reference, draft_id))
    conn.commit()
    if result.rowcount != 1:
        raise MetaSocialError('This draft cannot be approved in its current state.')


def publish_approved_draft(conn, draft_id):
    draft = conn.execute(
        "SELECT * FROM social_post_drafts WHERE draft_id=? AND status='approved'",
        (draft_id,),
    ).fetchone()
    if not draft:
        raise MetaSocialError('Only an approved draft can be published.')
    connection = conn.execute(
        'SELECT * FROM meta_social_connections WHERE connection_id=1'
    ).fetchone()
    if not connection:
        raise MetaSocialError('Connect the CareIL Facebook Page before publishing.')
    claimed = conn.execute('''
        UPDATE social_post_drafts SET status='publishing', updated_at=CURRENT_TIMESTAMP
        WHERE draft_id=? AND status='approved'
    ''', (draft_id,))
    conn.commit()
    if claimed.rowcount != 1:
        raise MetaSocialError('This draft is already being published.')
    token = _decrypt(connection['page_access_token_encrypted'])
    try:
        if draft.get('image_url'):
            result = _request_json(
                f"{connection['page_id']}/photos",
                method='POST',
                params={'url': draft['image_url'], 'caption': draft['message'], 'published': 'true'},
                access_token=token,
            )
            post_id = result.get('post_id') or result.get('id')
        else:
            result = _request_json(
                f"{connection['page_id']}/feed",
                method='POST', params={'message': draft['message']}, access_token=token,
            )
            post_id = result.get('id')
        if not post_id:
            raise MetaSocialError('Meta accepted the request but did not return a post ID.')
    except Exception as error:
        conn.execute('''
            UPDATE social_post_drafts SET status='failed', error_message=?,
                updated_at=CURRENT_TIMESTAMP WHERE draft_id=?
        ''', (str(error)[:1000], draft_id))
        conn.commit()
        raise
    conn.execute('''
        UPDATE social_post_drafts SET status='published', meta_post_id=?,
            published_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP,
            error_message=NULL WHERE draft_id=?
    ''', (post_id, draft_id))
    conn.commit()
    return post_id

import os
import sqlite3
import unittest
import urllib.parse
from unittest.mock import patch

from package.meta_social import (
    MetaSocialError,
    authorization_url,
    approve_draft,
    create_draft,
    publish_approved_draft,
    save_connection,
)


class MetaSocialTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = lambda cursor, row: {
            column[0]: row[index] for index, column in enumerate(cursor.description)
        }
        self.conn.executescript('''
            CREATE TABLE meta_social_connections (
                connection_id INTEGER PRIMARY KEY CHECK (connection_id = 1),
                page_id TEXT NOT NULL,
                page_name TEXT NOT NULL,
                page_access_token_encrypted TEXT NOT NULL,
                connected_by TEXT NOT NULL,
                granted_scopes TEXT,
                connected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE social_post_drafts (
                draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                image_url TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_by TEXT NOT NULL,
                approval_reference TEXT,
                approved_by TEXT,
                approved_at DATETIME,
                meta_post_id TEXT,
                published_at DATETIME,
                error_message TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        ''')

    def tearDown(self):
        self.conn.close()

    def test_draft_requires_approval_before_publish(self):
        draft_id = create_draft(self.conn, 'Hello CareIL', None, 'agent')
        with self.assertRaisesRegex(MetaSocialError, 'Only an approved draft'):
            publish_approved_draft(self.conn, draft_id)

    def test_approved_draft_publishes_and_records_meta_id(self):
        with patch.dict(os.environ, {'THERAPY_SECRET_KEY': 'test-secret', 'META_APP_SECRET': 'secret'}):
            save_connection(self.conn, {
                'id': '123', 'name': 'CareIL', 'access_token': 'page-token'
            }, 'owner')
            draft_id = create_draft(self.conn, 'Approved post', None, 'agent')
            approve_draft(self.conn, draft_id, 'owner', 'Chat approval 42')
            with patch('package.meta_social._request_json', return_value={'id': '123_456'}) as request_json:
                post_id = publish_approved_draft(self.conn, draft_id)
        row = self.conn.execute(
            'SELECT status, meta_post_id, approval_reference FROM social_post_drafts WHERE draft_id=?',
            (draft_id,),
        ).fetchone()
        self.assertEqual(post_id, '123_456')
        self.assertEqual(row['status'], 'published')
        self.assertEqual(row['meta_post_id'], '123_456')
        self.assertEqual(row['approval_reference'], 'Chat approval 42')
        request_json.assert_called_once()

    def test_image_url_must_be_public_https(self):
        with self.assertRaisesRegex(MetaSocialError, 'public HTTPS'):
            create_draft(self.conn, 'Post', 'http://localhost/image.png', 'agent')

    def test_business_login_url_uses_configuration_id(self):
        environment = {
            'META_APP_ID': 'app-123',
            'META_APP_SECRET': 'secret',
            'META_LOGIN_CONFIG_ID': 'config-456',
        }
        with patch.dict(os.environ, environment, clear=False):
            url = authorization_url('https://www.careil.net/meta/callback', 'state-token')
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(query['config_id'], ['config-456'])
        self.assertEqual(query['response_type'], ['code'])
        self.assertEqual(query['override_default_response_type'], ['true'])
        self.assertNotIn('scope', query)


if __name__ == '__main__':
    unittest.main()

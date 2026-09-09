import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_patient_schema_and_migration_include_profile_fields():
    source = (ROOT / 'package' / 'database.py').read_text(encoding='utf-8')
    for column in ('pat_gender', 'parent1_name', 'parent2_name'):
        assert column in source
    assert 'ensure_patient_profile_schema(conn)' in source


def test_patient_create_update_and_forms_include_profile_fields():
    api = (ROOT / 'package' / 'patient.py').read_text(encoding='utf-8')
    detail = (ROOT / 'templates' / 'patientform.html').read_text(encoding='utf-8')
    create = (ROOT / 'templates' / 'patient.html').read_text(encoding='utf-8')
    for field in ('pat_gender', 'parent1_name', 'parent2_name'):
        assert field in api
        assert 'name="%s"' % field in detail
        assert 'name="%s"' % field in create


def test_profile_field_translations_exist_in_both_languages():
    translations = json.loads((ROOT / 'Translate.json').read_text(encoding='utf-8'))
    for language in ('EN', 'HE'):
        for key in ('gender', 'parent1Name', 'parent2Name', 'genderFemale', 'genderMale'):
            assert translations[language][key]

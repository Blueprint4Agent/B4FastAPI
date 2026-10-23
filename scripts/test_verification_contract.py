"""Provider additions must not weaken any pinned consumer contract fragment."""

import copy
import unittest

from verification_contract import additive_contract


class ContractCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.consumer = {
            "openapi": "3.1.0",
            "info": {"title": "app", "version": "1"},
            "security": [{"Bearer": []}],
            "paths": {"/old": {"get": {"responses": {"200": {"description": "ok"}}}}},
            "components": {
                "schemas": {
                    "Old": {"type": "object", "properties": {"id": {"type": "integer"}}}
                },
                "securitySchemes": {"Bearer": {"type": "http", "scheme": "bearer"}},
            },
        }

    def test_new_path_method_and_unreferenced_components_are_additive(self):
        provider = copy.deepcopy(self.consumer)
        provider["paths"]["/new"] = {
            "get": {"responses": {"200": {"description": "new"}}}
        }
        provider["paths"]["/old"]["post"] = {
            "responses": {"201": {"description": "created"}}
        }
        provider["components"]["schemas"]["New"] = {"type": "string"}
        self.assertTrue(additive_contract(self.consumer, provider))
        self.assertTrue(additive_contract(self.consumer, self.consumer))

    def test_changed_or_removed_existing_guarantees_are_rejected(self):
        self.consumer["components"]["schemas"]["BooleanConst"] = {"const": True}
        mutations = [
            lambda p: p["components"]["schemas"]["BooleanConst"].update(const=1),
            lambda p: p["paths"].pop("/old"),
            lambda p: p["paths"]["/old"]["get"]["responses"].pop("200"),
            lambda p: p["paths"]["/old"].update(
                parameters=[{"name": "required", "in": "query", "required": True}]
            ),
            lambda p: p["components"]["schemas"]["Old"].update(required=["id"]),
            lambda p: p["components"]["schemas"]["Old"]["properties"]["id"].update(
                type="string"
            ),
            lambda p: p.update(security=[]),
            lambda p: p.update(servers=[{"url": "https://other.example"}]),
        ]
        for mutate in mutations:
            provider = copy.deepcopy(self.consumer)
            mutate(provider)
            self.assertFalse(additive_contract(self.consumer, provider))
        self.assertFalse(additive_contract({}, []))

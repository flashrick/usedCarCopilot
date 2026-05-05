from __future__ import annotations

import json
import unittest
from datetime import date

from app.ingestion.seed_loader import make_json_compatible
from app.valuation.service import compute_profile_valuation


class SeedLoaderTests(unittest.TestCase):
    def test_make_json_compatible_converts_valuation_date_for_raw_payload(self) -> None:
        profile = {
            "profile_id": "toyota-aqua-2015-2017-hybrid-s",
            "title": "2015-2017 Toyota Aqua Hybrid S",
            "brand": "Toyota",
            "model": "Aqua",
            "year_start": 2015,
            "year_end": 2017,
            "trim": "S",
            "engine_description": "1.5L petrol hybrid",
            "transmission": "cvt",
            "fuel_type": "petrol hybrid",
            "body_type": "hatchback",
            "maintenance_cost_band": "low",
            "base_msrp_nzd": 27990,
        }

        valuation = compute_profile_valuation(profile, as_of=date(2026, 5, 5))
        raw_payload = make_json_compatible({**profile, **valuation})

        self.assertEqual(raw_payload["valuation_as_of_date"], "2026-05-05")
        self.assertEqual(valuation["valuation_as_of_date"], date(2026, 5, 5))
        self.assertEqual(json.loads(json.dumps(raw_payload))["valuation_as_of_date"], "2026-05-05")


if __name__ == "__main__":
    unittest.main()

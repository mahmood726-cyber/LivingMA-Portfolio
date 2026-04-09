#!/usr/bin/env python3
"""
CT.gov Living Update Scanner
Checks all 39 living MA topics for newly posted trial results.

Uses the CT.gov API v2 (https://clinicaltrials.gov/api/v2/).
Writes scan_report.md and sets GITHUB_OUTPUT new_results=true if any new
results are found.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "mahmood.ahmad2@nhs.net")

# ---------------------------------------------------------------------------
# All 39 topics.  "known" = NCT IDs already accounted for in the living MA.
# Any completed trial with results NOT in this list is flagged as new.
# ---------------------------------------------------------------------------
TOPICS = [
    {
        "name": "PFA in AF",
        "search": "pulsed field ablation",
        "known": ["NCT04612244", "NCT05534581", "NCT04198701"],
    },
    {
        "name": "Watchman vs Amulet",
        "search": "left atrial appendage Watchman Amulet",
        "known": ["NCT02879448", "NCT03399851"],
    },
    {
        "name": "Tricuspid TEER",
        "search": "triclip PASCAL tricuspid",
        "known": ["NCT03904147"],
    },
    {
        "name": "Inclisiran",
        "search": "inclisiran",
        "known": ["NCT03397121", "NCT03399370", "NCT03400800", "NCT03705234"],
    },
    {
        "name": "Tirzepatide",
        "search": "tirzepatide",
        "known": ["NCT04184622", "NCT04657003", "NCT04657016", "NCT04660643"],
    },
    {
        "name": "Semaglutide HFpEF",
        "search": "semaglutide heart failure",
        "known": ["NCT04788511", "NCT04916470"],
    },
    {
        "name": "Leadless Pacing",
        "search": "leadless pacemaker micra aveir",
        "known": ["NCT02004873"],
    },
    {
        "name": "CSP vs CRT",
        "search": "conduction system pacing left bundle branch pacing",
        "known": ["NCT04561778", "NCT05572736"],
    },
    {
        "name": "Coronary IVL",
        "search": "intravascular lithotripsy coronary",
        "known": [],
    },
    {
        "name": "Omecamtiv Mecarbil",
        "search": "omecamtiv mecarbil",
        "known": ["NCT02929329", "NCT03759392"],
    },
    {
        "name": "CT-FFR",
        "search": "CT-FFR fractional flow reserve computed tomography",
        "known": ["NCT03702244", "NCT03187639"],
    },
    {
        "name": "Vericiguat",
        "search": "vericiguat",
        "known": ["NCT02861534", "NCT03547583"],
    },
    {
        "name": "Sotagliflozin",
        "search": "sotagliflozin",
        "known": ["NCT03315143", "NCT03521934"],
    },
    {
        "name": "T-DXd Breast",
        "search": "trastuzumab deruxtecan breast",
        "known": [
            "NCT03529110",
            "NCT03734029",
            "NCT03523585",
            "NCT04494425",
        ],
    },
    {
        "name": "Osimertinib NSCLC",
        "search": "osimertinib lung cancer",
        "known": [
            "NCT02296125",
            "NCT04035486",
            "NCT02511106",
            "NCT02151981",
        ],
    },
    {
        "name": "Anti-Amyloid AD",
        "search": "lecanemab donanemab",
        "known": ["NCT03887455", "NCT04437511"],
    },
    {
        "name": "Resmetirom MASH",
        "search": "resmetirom",
        "known": ["NCT03900429", "NCT04197479"],
    },
    {
        "name": "Sotatercept PAH",
        "search": "sotatercept pulmonary",
        "known": ["NCT04576988", "NCT04811092", "NCT04896008"],
    },
    {
        "name": "Icosapent Ethyl",
        "search": "icosapent ethyl",
        "known": ["NCT01492361", "NCT02104817"],
    },
    {
        "name": "Semaglutide CKD",
        "search": "semaglutide kidney",
        "known": ["NCT03819153"],
    },
    {
        "name": "Ticagrelor Mono",
        "search": "ticagrelor monotherapy",
        "known": ["NCT02270242", "NCT02494895", "NCT01813435"],
    },
    {
        "name": "DCB PAD",
        "search": "drug coated balloon femoropopliteal",
        "known": ["NCT01566461"],
    },
    {
        "name": "Orforglipron",
        "search": "orforglipron",
        "known": ["NCT05048719", "NCT05051579"],
    },
    {
        "name": "K+ Binders",
        "search": "patiromer sodium zirconium cyclosilicate",
        "known": ["NCT03888066"],
    },
    {
        "name": "Empagliflozin MI",
        "search": "empagliflozin myocardial infarction",
        "known": ["NCT04509674", "NCT03087773"],
    },
    {
        "name": "Obesity NMA",
        "search": "tirzepatide semaglutide orforglipron obesity",
        "known": [],
    },
    {
        "name": "Dupilumab COPD",
        "search": "dupilumab COPD",
        "known": ["NCT03930732", "NCT04456673"],
    },
    {
        "name": "Tezepelumab Asthma",
        "search": "tezepelumab asthma",
        "known": ["NCT03347279", "NCT02054130"],
    },
    {
        "name": "KRAS G12C NSCLC",
        "search": "sotorasib adagrasib",
        "known": ["NCT04303780", "NCT04685135"],
    },
    {
        "name": "Sacituzumab Breast",
        "search": "sacituzumab govitecan breast",
        "known": ["NCT02574455", "NCT03901339"],
    },
    {
        "name": "Sparsentan IgAN",
        "search": "sparsentan",
        "known": ["NCT03762850"],
    },
    {
        "name": "Dapagliflozin Acute HF",
        "search": "dapagliflozin acute heart failure",
        "known": ["NCT04363697", "NCT04298229"],
    },
    {
        "name": "Enfortumab UC",
        "search": "enfortumab vedotin urothelial",
        "known": ["NCT03474107", "NCT04223856"],
    },
    {
        "name": "Pembrolizumab Adj Melanoma",
        "search": "pembrolizumab melanoma adjuvant",
        "known": ["NCT03553836", "NCT03897881"],
    },
    {
        "name": "Iptacopan",
        "search": "iptacopan",
        "known": ["NCT04558918", "NCT04578834"],
    },
    {
        "name": "Bimekizumab Psoriasis",
        "search": "bimekizumab psoriasis",
        "known": [
            "NCT03370133",
            "NCT03412747",
            "NCT03410992",
            "NCT03536884",
        ],
    },
    {
        "name": "PAH NMA",
        "search": "sotatercept selexipag macitentan pulmonary hypertension",
        "known": [],
    },
    {
        "name": "HFrEF NMA",
        "search": "empagliflozin dapagliflozin heart failure reduced",
        "known": [],
    },
    {
        "name": "Antiplatelet NMA",
        "search": "ticagrelor monotherapy clopidogrel monotherapy PCI",
        "known": [],
    },
]

CTGOV_API = "https://clinicaltrials.gov/api/v2/studies"
REQUEST_TIMEOUT = 30  # seconds


def check_topic(topic: dict) -> list[dict]:
    """
    Query CT.gov for completed trials with results that are not in the
    topic's known list.  Returns a list of dicts with keys:
      nct_id, title, results_date, ct_link
    """
    new_results = []
    try:
        params = {
            "query.intr": topic["search"],
            "filter.overallStatus": "COMPLETED",
            "pageSize": 100,
            "fields": ",".join([
                "NCTId",
                "BriefTitle",
                "HasResults",
                "ResultsFirstPostDate",
                "OverallStatus",
                "CompletionDate",
            ]),
        }
        resp = requests.get(CTGOV_API, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        studies = data.get("studies", [])

        for study in studies:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status = proto.get("statusModule", {})

            nct_id = ident.get("nctId", "")
            if not nct_id:
                continue

            # hasResults can live in multiple places depending on API version
            has_results = (
                status.get("hasResults", False)
                or study.get("hasResults", False)
            )

            if has_results and nct_id not in topic["known"]:
                title = ident.get("briefTitle", "Unknown title")
                results_date = (
                    status.get("resultsFirstPostDateStruct", {}).get("date", "")
                )
                new_results.append(
                    {
                        "nct_id": nct_id,
                        "title": title[:120],
                        "results_date": results_date,
                        "ct_link": (
                            f"https://clinicaltrials.gov/study/{nct_id}?tab=results"
                        ),
                    }
                )
    except requests.exceptions.RequestException as exc:
        print(f"  [WARN] Network error for topic '{topic['name']}': {exc}")
    except Exception as exc:
        print(f"  [WARN] Unexpected error for topic '{topic['name']}': {exc}")

    return new_results


def build_report(all_new: dict, scan_ts: str) -> str:
    """Build a Markdown report from the scan results."""
    total_new = sum(len(v) for v in all_new.values())

    lines = [
        f"# CT.gov Living Update Scan — {scan_ts}",
        "",
        f"| | |",
        f"|---|---|",
        f"| **Alert email** | {ALERT_EMAIL} |",
        f"| **Topics scanned** | {len(TOPICS)} |",
        f"| **Topics with new results** | {len(all_new)} |",
        f"| **New trial results found** | {total_new} |",
        "",
    ]

    if all_new:
        lines += [
            "## New Results Found",
            "",
            "> Review each trial and update the relevant living meta-analysis.",
            "",
        ]
        for topic_name, results in all_new.items():
            lines.append(f"### {topic_name}")
            lines.append("")
            for r in results:
                lines.append(f"- **[{r['nct_id']}]({r['ct_link']})**: {r['title']}")
                if r["results_date"]:
                    lines.append(f"  - Results posted: {r['results_date']}")
            lines.append("")
        lines += [
            "---",
            "",
            "**Action required:** Update each living meta-analysis with the new results above.",
        ]
    else:
        lines += [
            "## No New Results",
            "",
            "All 39 topics are up to date. No new trial results have been posted "
            "since the last scan.",
        ]

    return "\n".join(lines) + "\n"


def set_github_output(key: str, value: str) -> None:
    """Write a key=value pair to $GITHUB_OUTPUT (GitHub Actions)."""
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"{key}={value}\n")
    else:
        # Local run: print to stdout for visibility
        print(f"[GITHUB_OUTPUT] {key}={value}")


def main() -> None:
    scan_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"CT.gov Living Update Scanner — {scan_ts}")
    print(f"Scanning {len(TOPICS)} topics...\n")

    all_new: dict[str, list[dict]] = {}
    for idx, topic in enumerate(TOPICS, start=1):
        prefix = f"[{idx:02d}/{len(TOPICS)}]"
        new = check_topic(topic)
        if new:
            all_new[topic["name"]] = new
            print(f"  {prefix} NEW  {topic['name']} — {len(new)} new result(s)")
            for r in new:
                print(f"           {r['nct_id']}: {r['title'][:80]}")
        else:
            print(f"  {prefix} OK   {topic['name']}")

    # Write Markdown report (picked up by the email action and artifact upload)
    report_path = "scan_report.md"
    report = build_report(all_new, scan_ts)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"\nReport written to {report_path}")

    # Signal the workflow whether to send the alert email
    if all_new:
        total_new = sum(len(v) for v in all_new.values())
        print(f"\nALERT: {len(all_new)} topic(s) with {total_new} new result(s) found.")
        set_github_output("new_results", "true")
    else:
        print(f"\nAll {len(TOPICS)} topics are up to date.")
        set_github_output("new_results", "false")


if __name__ == "__main__":
    main()

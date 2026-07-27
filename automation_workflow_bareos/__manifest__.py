{
    "name": "Automation Workflow (Bareos)",
    "version": "19.0.2.0.0",
    "summary": "Create TODO activities on incoming messages for any model",
    "author": "Bareos GmbH & Co. KG",
    "license": "LGPL-3",
    "category": "Discuss",
    "depends": [
        "base_automation",
        "mail",
        "crm",
        "sale",
        "account",
        "project",
    ],
    "data": [
        "data/base_automation_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

"""Нестандарти process: stage catalog and transition graph.

Design doc: BP_STANDARTY_2026_PROCESS_DESIGN.md.

Same template as standard.py (the two diagram pages are ~95% identical), kept as an
independent file/process_type since the user may diverge them during live correction.
role_owner comes from this page's own row-legend (same method as standard.py) — one
stage (vovr_for_voe) genuinely differs between the two pages' legends, kept as-is.
stage_key prefixed with nonstd_.

Draft quality — decision directions inferred from
stage-name semantics, not from explicit edge labels. See design doc "[ЗДОГАД]" list.
"""

from backend.app.processes.definition import ProcessDefinition, StageRow

# (display_code, stage_key, name, role_owner, is_decision)
STAGES: list[StageRow] = [
    ("1", "nonstd_new_order_detected", "Виявлення нового замовлення", "Sales", False),
    ("2", "nonstd_order_analysis_crm_registration", "Аналіз та реєстрація замовлення в CRM", "РМ", False),
    ("3", "nonstd_order_schedule_entry", "Внесення замовлення в графік робіт", "РМ", False),
    ("4", "nonstd_object_warehouse_1c_creation", "Створення складу обʼєкту в 1С", "РМ", False),
    ("5", "nonstd_breaker_to_object_warehouse", "Перемістити автоматичний вимикач на склад обʼєкта", "РМ", False),
    (
        "5b",
        "nonstd_breaker_retrieval_for_control",
        "Отримати автоматичний вимикач для проходження вхідного контролю",
        "Менеджер з документообігу",
        False,
    ),
    (
        "6",
        "nonstd_voe_inspection_letter_prep",
        "Підготувати лист для проходження вх. контролю у ВОЕ",
        "Менеджер з документообігу",
        False,
    ),
    (
        "7",
        "nonstd_voe_registration_number",
        "Отримати реєстраційний номер для проходження вх. контролю",
        "Менеджер з документообігу",
        False,
    ),
    (
        "8",
        "nonstd_breaker_handover_to_voe",
        "Здати авт. вимикач у ВОЕ на вх. контроль",
        "Менеджер з документообігу",
        False,
    ),
    ("9", "nonstd_object_analysis", "Аналіз обʼєкту", "Виконроб", False),
    ("10", "nonstd_vovr_to_estimator", "ВОВР кошториснику", "РМ", False),
    ("11", "nonstd_team_payroll_calc", "Розрахунок ЗП команди", "Кошторисник", False),
    ("12", "nonstd_breaker_pickup_from_voe", "Забрати авт. вимикач з вх. контролю", "Менеджер з документообігу", False),
    ("13", "nonstd_materials_availability_check", "Наявність матеріалів", "РМ", True),
    ("13b", "nonstd_materials_procurement", "Закупівля", "Менеджер з постачання", False),
    (
        "13c",
        "nonstd_pm_full_kit_notification",
        "Повідомлення РМ про повне комплектування обєкту",
        "Менеджер з постачання",
        False,
    ),
    ("14", "nonstd_materials_to_object_warehouse", "Переміщення матеріалів на склад обєкта", "РМ", False),
    ("15", "nonstd_start_date", "Дата старту", "КПМВ", False),
    ("16", "nonstd_disconnection_needed_check", "Потрібно відключення", "РМ", True),
    ("16b", "nonstd_disconnection_letter", "Лист про відключення", "Менеджер з документообігу", False),
    (
        "17",
        "nonstd_inbound_control_act_formation",
        "Сформувати акт вхідного контролю",
        "Менеджер з документообігу",
        False,
    ),
    ("18", "nonstd_object_kitting", "Комплектування обєкту", "Працівник складу", False),
    ("19", "nonstd_materials_receipt", "Прийом матеріалів", "Виконроб", False),
    ("20", "nonstd_design_docs_for_works", "Отримання проектної документації для виконання робіт", "Виконроб", False),
    ("21", "nonstd_loading_to_object", "Завантаження на обʼєкт", "Майстер", False),
    ("22", "nonstd_electrical_installation", "Електромонтажні роботи", "Майстер", False),
    ("23", "nonstd_photo_report_and_vovr", "Фотозвіт та ВОВР", "Майстер", False),
    ("24", "nonstd_materials_to_main_warehouse", "Здача матеріалів на головний склад", "Майстер", False),
    ("25", "nonstd_materials_receipt_main", "Приймання матеріалів", "Працівник складу", False),
    ("26", "nonstd_materials_return_form", "Бланк на повернення матеріалів", "Працівник складу", False),
    (
        "27",
        "nonstd_leftover_materials_to_main",
        "Переміщення залишків матеріалів зі складу обєкта на головний",
        "РМ",
        False,
    ),
    ("28", "nonstd_work_completion_letter", "Лист про завершення робіт", "Менеджер з документообігу", False),
    ("29", "nonstd_vovr_for_voe", "ВОВР для ВОЕ", "Кошторисник", False),
    ("30", "nonstd_vovr_approved_check", "Погодили ВОВР", "ВОЕ", True),
    ("31", "nonstd_quality_check_act", "Акт перевірки якості", "ВОЕ", False),
    ("32", "nonstd_quality_agreement_check", "Погоджуєм?", "РМ", True),
    (
        "33",
        "nonstd_quality_response_letter",
        "Лист-відповідь на акт перевірки якості",
        "Менеджер з документообігу",
        False,
    ),
    ("34", "nonstd_response_agreed_check", "Погодили відповідь", "ВОЕ", True),
    ("35", "nonstd_rework_planning", "Планування", "КПМВ", False),
    ("36", "nonstd_object_rework", "Доопрацювання обєкту", "Майстер", False),
    ("37", "nonstd_completion_acts_signing", "Підписання Актів виконаних робіт", "РМ", False),
    ("38", "nonstd_act_handover_to_accounting", "Передача Акту в бухгалтерію", "Менеджер з документообігу", False),
    ("39", "nonstd_materials_writeoff", "Списання фактично використаних матеріалів", "Бухгалтер", False),
]

TRANSITIONS: dict[str, dict] = {
    "nonstd_new_order_detected": {"next": "nonstd_order_analysis_crm_registration"},
    "nonstd_order_analysis_crm_registration": {"next": "nonstd_order_schedule_entry"},
    "nonstd_order_schedule_entry": {"next": "nonstd_object_warehouse_1c_creation"},
    "nonstd_object_warehouse_1c_creation": {"next": "nonstd_breaker_to_object_warehouse"},
    "nonstd_breaker_to_object_warehouse": {"next": "nonstd_breaker_retrieval_for_control"},
    "nonstd_breaker_retrieval_for_control": {"next": "nonstd_voe_inspection_letter_prep"},
    "nonstd_voe_inspection_letter_prep": {"next": "nonstd_voe_registration_number"},
    "nonstd_voe_registration_number": {"next": "nonstd_breaker_handover_to_voe"},
    "nonstd_breaker_handover_to_voe": {"next": "nonstd_object_analysis"},
    "nonstd_object_analysis": {"next": "nonstd_vovr_to_estimator"},
    "nonstd_vovr_to_estimator": {"next": "nonstd_team_payroll_calc"},
    "nonstd_team_payroll_calc": {"next": "nonstd_breaker_pickup_from_voe"},
    "nonstd_breaker_pickup_from_voe": {"next": "nonstd_materials_availability_check"},
    "nonstd_materials_availability_check": {
        "yes": "nonstd_materials_to_object_warehouse",
        "no": "nonstd_materials_procurement",
    },
    "nonstd_materials_procurement": {"next": "nonstd_pm_full_kit_notification"},
    "nonstd_pm_full_kit_notification": {"next": "nonstd_materials_to_object_warehouse"},
    "nonstd_materials_to_object_warehouse": {"next": "nonstd_start_date"},
    "nonstd_start_date": {"next": "nonstd_disconnection_needed_check"},
    "nonstd_disconnection_needed_check": {
        "yes": "nonstd_disconnection_letter",
        "no": "nonstd_inbound_control_act_formation",
    },
    "nonstd_disconnection_letter": {"next": "nonstd_inbound_control_act_formation"},
    "nonstd_inbound_control_act_formation": {"next": "nonstd_object_kitting"},
    "nonstd_object_kitting": {"next": "nonstd_materials_receipt"},
    "nonstd_materials_receipt": {"next": "nonstd_design_docs_for_works"},
    "nonstd_design_docs_for_works": {"next": "nonstd_loading_to_object"},
    "nonstd_loading_to_object": {"next": "nonstd_electrical_installation"},
    "nonstd_electrical_installation": {"next": "nonstd_photo_report_and_vovr"},
    "nonstd_photo_report_and_vovr": {"next": "nonstd_materials_to_main_warehouse"},
    "nonstd_materials_to_main_warehouse": {"next": "nonstd_materials_receipt_main"},
    "nonstd_materials_receipt_main": {"next": "nonstd_materials_return_form"},
    "nonstd_materials_return_form": {"next": "nonstd_leftover_materials_to_main"},
    "nonstd_leftover_materials_to_main": {"next": "nonstd_work_completion_letter"},
    "nonstd_work_completion_letter": {"next": "nonstd_vovr_for_voe"},
    "nonstd_vovr_for_voe": {"next": "nonstd_vovr_approved_check"},
    "nonstd_vovr_approved_check": {"yes": "nonstd_completion_acts_signing", "no": "nonstd_quality_check_act"},
    "nonstd_quality_check_act": {"next": "nonstd_quality_agreement_check"},
    "nonstd_quality_agreement_check": {"yes": "nonstd_rework_planning", "no": "nonstd_quality_response_letter"},
    "nonstd_quality_response_letter": {"next": "nonstd_response_agreed_check"},
    "nonstd_response_agreed_check": {"yes": "nonstd_completion_acts_signing", "no": "nonstd_rework_planning"},
    "nonstd_rework_planning": {"next": "nonstd_object_rework"},
    "nonstd_object_rework": {"next": "nonstd_vovr_for_voe"},
    "nonstd_completion_acts_signing": {"next": "nonstd_act_handover_to_accounting"},
    "nonstd_act_handover_to_accounting": {"next": "nonstd_materials_writeoff"},
    "nonstd_materials_writeoff": {"terminal": "completed"},
}

PROCESS = ProcessDefinition(
    name="Нестандарти",
    stages=STAGES,
    transitions=TRANSITIONS,
)

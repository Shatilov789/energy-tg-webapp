"""Стандарти process: stage catalog and transition graph.

Design doc: BP_STANDARTY_2026_PROCESS_DESIGN.md.

Rough draft parsed from "БП Стандарти 2026.drawio" (page "Стандарти"). role_owner comes
from the diagram's own row-legend (11 role labels positioned as UserObject-wrapped cells
to the side of the flow, matched to each stage by Y-row) — not a free-text swimlane like
СЕС/АСКОЕ, but real data, not a semantic guess.
stage_key prefixed with std_ (Stage.stage_key is globally unique).

Draft quality — decision directions inferred from
stage-name semantics, not from explicit edge labels. See design doc "[ЗДОГАД]" list.
"""

from backend.app.processes.definition import ProcessDefinition, StageRow

# (display_code, stage_key, name, role_owner, is_decision)
STAGES: list[StageRow] = [
    ("1", "std_new_order_detected", "Виявлення нового замовлення", "Sales", False),
    ("2", "std_order_analysis_crm_registration", "Аналіз та реєстрація замовлення в CRM", "РМ", False),
    ("3", "std_order_schedule_entry", "Внесення замовлення в графік робіт", "РМ", False),
    ("4", "std_object_warehouse_1c_creation", "Створення складу обʼєкту в 1С", "РМ", False),
    ("5", "std_breaker_to_object_warehouse", "Перемістити автоматичний вимикач на склад обʼєкта", "РМ", False),
    (
        "5b",
        "std_breaker_retrieval_for_control",
        "Отримати автоматичний вимикач для проходження вхідного контролю",
        "Менеджер з документообігу",
        False,
    ),
    (
        "6",
        "std_voe_inspection_letter_prep",
        "Підготувати лист для проходження вх. контролю у ВОЕ",
        "Менеджер з документообігу",
        False,
    ),
    (
        "7",
        "std_voe_registration_number",
        "Отримати реєстраційний номер для проходження вх. контролю",
        "Менеджер з документообігу",
        False,
    ),
    (
        "8",
        "std_breaker_handover_to_voe",
        "Здати авт. вимикач у ВОЕ на вх. контроль",
        "Менеджер з документообігу",
        False,
    ),
    ("9", "std_object_analysis", "Аналіз обʼєкту", "Виконроб", False),
    ("10", "std_vovr_to_estimator", "ВОВР кошториснику", "РМ", False),
    ("11", "std_team_payroll_calc", "Розрахунок ЗП команди", "Кошторисник", False),
    ("12", "std_breaker_pickup_from_voe", "Забрати авт. вимикач з вх. контролю", "Менеджер з документообігу", False),
    ("13", "std_materials_availability_check", "Наявність матеріалів", "РМ", True),
    ("13b", "std_materials_procurement", "Закупівля", "Менеджер з постачання", False),
    (
        "13c",
        "std_pm_full_kit_notification",
        "Повідомлення РМ про повне комплектування обєкту",
        "Менеджер з постачання",
        False,
    ),
    ("14", "std_materials_to_object_warehouse", "Переміщення матеріалів на склад обєкта", "РМ", False),
    ("15", "std_start_date", "Дата старту", "КПМВ", False),
    ("16", "std_disconnection_needed_check", "Потрібно відключення", "РМ", True),
    ("16b", "std_disconnection_letter", "Лист про відключення", "Менеджер з документообігу", False),
    ("17", "std_inbound_control_act_formation", "Сформувати акт вхідного контролю", "Менеджер з документообігу", False),
    ("18", "std_object_kitting", "Комплектування обєкту", "Працівник складу", False),
    ("19", "std_materials_receipt", "Прийом матеріалів", "Виконроб", False),
    ("20", "std_design_docs_for_works", "Отримання проектної документації для виконання робіт", "Виконроб", False),
    ("21", "std_loading_to_object", "Завантаження на обʼєкт", "Майстер", False),
    ("22", "std_electrical_installation", "Електромонтажні роботи", "Майстер", False),
    ("23", "std_photo_report_and_vovr", "Фотозвіт та ВОВР", "Майстер", False),
    ("24", "std_materials_to_main_warehouse", "Здача матеріалів на головний склад", "Майстер", False),
    ("25", "std_materials_receipt_main", "Приймання матеріалів", "Працівник складу", False),
    ("26", "std_materials_return_form", "Бланк на повернення матеріалів", "Працівник складу", False),
    (
        "27",
        "std_leftover_materials_to_main",
        "Переміщення залишків матеріалів зі складу обєкта на головний",
        "РМ",
        False,
    ),
    ("28", "std_work_completion_letter", "Лист про завершення робіт", "Менеджер з документообігу", False),
    ("29", "std_vovr_for_voe", "ВОВР для ВОЕ", "РМ", False),
    ("30", "std_vovr_approved_check", "Погодили ВОВР", "ВОЕ", True),
    ("31", "std_quality_check_act", "Акт перевірки якості", "ВОЕ", False),
    ("32", "std_quality_agreement_check", "Погоджуєм?", "РМ", True),
    ("33", "std_quality_response_letter", "Лист-відповідь на акт перевірки якості", "Менеджер з документообігу", False),
    ("34", "std_response_agreed_check", "Погодили відповідь", "ВОЕ", True),
    ("35", "std_rework_planning", "Планування", "КПМВ", False),
    ("36", "std_object_rework", "Доопрацювання обєкту", "Майстер", False),
    ("37", "std_completion_acts_signing", "Підписання Актів виконаних робіт", "РМ", False),
    ("38", "std_act_handover_to_accounting", "Передача Акту в бухгалтерію", "Менеджер з документообігу", False),
    ("39", "std_materials_writeoff", "Списання фактично використаних матеріалів", "Бухгалтер", False),
]

TRANSITIONS: dict[str, dict] = {
    "std_new_order_detected": {"next": "std_order_analysis_crm_registration"},
    "std_order_analysis_crm_registration": {"next": "std_order_schedule_entry"},
    "std_order_schedule_entry": {"next": "std_object_warehouse_1c_creation"},
    "std_object_warehouse_1c_creation": {"next": "std_breaker_to_object_warehouse"},
    "std_breaker_to_object_warehouse": {"next": "std_breaker_retrieval_for_control"},
    "std_breaker_retrieval_for_control": {"next": "std_voe_inspection_letter_prep"},
    "std_voe_inspection_letter_prep": {"next": "std_voe_registration_number"},
    "std_voe_registration_number": {"next": "std_breaker_handover_to_voe"},
    "std_breaker_handover_to_voe": {"next": "std_object_analysis"},
    "std_object_analysis": {"next": "std_vovr_to_estimator"},
    "std_vovr_to_estimator": {"next": "std_team_payroll_calc"},
    "std_team_payroll_calc": {"next": "std_breaker_pickup_from_voe"},
    "std_breaker_pickup_from_voe": {"next": "std_materials_availability_check"},
    "std_materials_availability_check": {
        "yes": "std_materials_to_object_warehouse",
        "no": "std_materials_procurement",
    },
    "std_materials_procurement": {"next": "std_pm_full_kit_notification"},
    "std_pm_full_kit_notification": {"next": "std_materials_to_object_warehouse"},
    "std_materials_to_object_warehouse": {"next": "std_start_date"},
    "std_start_date": {"next": "std_disconnection_needed_check"},
    "std_disconnection_needed_check": {
        "yes": "std_disconnection_letter",
        "no": "std_inbound_control_act_formation",
    },
    "std_disconnection_letter": {"next": "std_inbound_control_act_formation"},
    "std_inbound_control_act_formation": {"next": "std_object_kitting"},
    "std_object_kitting": {"next": "std_materials_receipt"},
    "std_materials_receipt": {"next": "std_design_docs_for_works"},
    "std_design_docs_for_works": {"next": "std_loading_to_object"},
    "std_loading_to_object": {"next": "std_electrical_installation"},
    "std_electrical_installation": {"next": "std_photo_report_and_vovr"},
    "std_photo_report_and_vovr": {"next": "std_materials_to_main_warehouse"},
    "std_materials_to_main_warehouse": {"next": "std_materials_receipt_main"},
    "std_materials_receipt_main": {"next": "std_materials_return_form"},
    "std_materials_return_form": {"next": "std_leftover_materials_to_main"},
    "std_leftover_materials_to_main": {"next": "std_work_completion_letter"},
    "std_work_completion_letter": {"next": "std_vovr_for_voe"},
    "std_vovr_for_voe": {"next": "std_vovr_approved_check"},
    "std_vovr_approved_check": {"yes": "std_completion_acts_signing", "no": "std_quality_check_act"},
    "std_quality_check_act": {"next": "std_quality_agreement_check"},
    "std_quality_agreement_check": {"yes": "std_rework_planning", "no": "std_quality_response_letter"},
    "std_quality_response_letter": {"next": "std_response_agreed_check"},
    "std_response_agreed_check": {"yes": "std_completion_acts_signing", "no": "std_rework_planning"},
    "std_rework_planning": {"next": "std_object_rework"},
    "std_object_rework": {"next": "std_vovr_for_voe"},
    "std_completion_acts_signing": {"next": "std_act_handover_to_accounting"},
    "std_act_handover_to_accounting": {"next": "std_materials_writeoff"},
    "std_materials_writeoff": {"terminal": "completed"},
}

PROCESS = ProcessDefinition(
    name="Стандарти",
    stages=STAGES,
    transitions=TRANSITIONS,
)

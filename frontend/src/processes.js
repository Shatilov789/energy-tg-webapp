import {
  IconBolt,
  IconBriefcase,
  IconBuildingFactory2,
  IconGavel,
  IconPlug,
  IconSun,
} from '@tabler/icons-react';

// Keys match ProcessDefinition.name on the backend (backend/app/processes/registry.py).
export const PROCESSES = [
  { key: 'СЕС', label: 'СЕС', hint: 'будівництво сонячних електростанцій', icon: IconSun },
  { key: 'АСКОЕ', label: 'АСКОЕ', hint: 'автоматизований облік електроенергії', icon: IconBolt },
  { key: 'Стандарти', label: 'Стандарти', hint: 'стандартне приєднання', icon: IconPlug },
  { key: 'Нестандарти', label: 'Нестандарти', hint: 'нестандартне приєднання', icon: IconBuildingFactory2 },
  { key: 'ІП', label: 'ІП', hint: 'інвестиційна програма', icon: IconGavel },
  { key: 'Комерція', label: 'Комерція', hint: 'комерційний процес продажів', icon: IconBriefcase },
];

export const DEAL_STATUS_LABELS = { active: 'В роботі', closed: 'Закрита', completed: 'Завершена' };

export const STAGE_STATUS_LABELS = {
  pending: 'Очікує',
  in_progress: 'В роботі',
  done: 'Виконано',
  skipped: 'Пропущено',
};

export function getProcessIcon(processType) {
  return PROCESSES.find(process => process.key === processType)?.icon ?? IconSun;
}

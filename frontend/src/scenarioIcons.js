import {
  IconBuildingFactory,
  IconLineDashed,
  IconBolt,
  IconTool,
  IconClipboardCheck,
  IconFileText,
} from '@tabler/icons-react';

const SCENARIO_ICONS = {
  'Подстанция': { icon: IconBuildingFactory, cls: 'ci-a' },
  'КЛ линия': { icon: IconLineDashed, cls: 'ci-b' },
  'Трансформатор': { icon: IconBolt, cls: 'ci-r' },
  'Ремонт': { icon: IconTool, cls: 'ci-g' },
  'Проверка оборудования': { icon: IconClipboardCheck, cls: 'ci-p' },
};

export function getScenarioIcon(name) {
  return SCENARIO_ICONS[name] || { icon: IconFileText, cls: 'ci-a' };
}

import {
  IconBuildingFactory,
  IconLineDashed,
  IconBolt,
  IconTool,
  IconClipboardCheck,
  IconFileText,
} from '@tabler/icons-react';

const SCENARIO_ICONS = {
  'Підстанція': { icon: IconBuildingFactory, cls: 'ci-a' },
  'КЛ лінія': { icon: IconLineDashed, cls: 'ci-b' },
  'Трансформатор': { icon: IconBolt, cls: 'ci-r' },
  'Ремонт': { icon: IconTool, cls: 'ci-g' },
  'Перевірка обладнання': { icon: IconClipboardCheck, cls: 'ci-p' },
};

export function getScenarioIcon(name) {
  return SCENARIO_ICONS[name] || { icon: IconFileText, cls: 'ci-a' };
}

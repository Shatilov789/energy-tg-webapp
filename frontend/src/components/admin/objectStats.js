export function getProgress(obj) {
  const stepsCount = obj.scenario?.steps?.length || 0;
  const answersCount = obj.answers?.length || 0;
  const pct = stepsCount > 0 ? Math.round((answersCount / stepsCount) * 100) : 0;
  return { stepsCount, answersCount, pct };
}

export function isFullyAnswered(obj) {
  const { stepsCount, answersCount } = getProgress(obj);
  return stepsCount > 0 && answersCount >= stepsCount;
}

export function objectsWord(count) {
  if (count === 1) return 'обʼєкт';
  return count < 5 ? 'обʼєкти' : 'обʼєктів';
}

export function buildMetrics(objects) {
  const completed = objects.filter(o => o.status === 'completed').length;
  const inProgress = objects.length - completed;

  let answered = 0;
  let questions = 0;
  objects.forEach(obj => {
    const { stepsCount, answersCount } = getProgress(obj);
    answered += answersCount;
    questions += stepsCount;
  });
  const overallPct = questions > 0 ? Math.round((answered / questions) * 100) : 0;
  const overdue = objects.filter(o => getProgress(o).pct === 0 && o.status !== 'completed').length;

  return [
    { label: 'Виконано', value: `${overallPct}%`, sub: 'середній прогрес', color: 'var(--acc)' },
    { label: 'Обʼєктів', value: inProgress, sub: 'в роботі', color: 'var(--acc2)' },
    { label: 'Прострочено', value: overdue, sub: 'потребують уваги', color: 'var(--err)' },
    { label: 'Завершено', value: completed, sub: 'інспекцій', color: 'var(--ok)' },
  ];
}

export function groupByWorker(objects) {
  const byWorker = {};
  const unassigned = [];
  for (const obj of objects) {
    if (!obj.workers || obj.workers.length === 0) {
      unassigned.push(obj);
      continue;
    }
    for (const worker of obj.workers) {
      byWorker[worker.user_id] ??= [];
      if (!byWorker[worker.user_id].some(o => o.id === obj.id)) {
        byWorker[worker.user_id].push(obj);
      }
    }
  }
  return { byWorker, unassigned };
}

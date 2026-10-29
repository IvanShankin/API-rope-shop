export const reviewFilters = { all: 'Все', new: 'На проверке', confirmed: 'Одобрены', rejected: 'Отклонены' };
export const reviewStatuses = { new: 'На проверке', confirmed: 'Одобрен', rejected: 'Отклонён' };

export function reviewPublication(item) {
  if (item.status === 'confirmed') return item.is_published === true ? 'Показывается на сайте' : 'Скрыт: публикация выключена';
  if (item.status === 'new') return 'Скрыт: ожидает одобрения';
  if (item.status === 'rejected') return 'Скрыт: отзыв отклонён';
  return 'Публикация не подтверждена';
}

export function reviewCounts(items) {
  const counts = { all: items.length, new: 0, confirmed: 0, rejected: 0 };
  for (const item of items) if (Object.hasOwn(reviewStatuses, item.status)) counts[item.status]++;
  return counts;
}

export function reviewRecords(items, filter = 'all') {
  return items.filter(item => filter === 'all' || item.status === filter).map(item => ({
    id: item.id,
    label: `${item.author_name} · ${reviewStatuses[item.status] || 'Статус неизвестен'}`,
    detail: `${reviewPublication(item)} · ${item.rating == null ? 'Без оценки' : `${item.rating} / 5`}`,
    search: (item.translations || []).map(translation => translation.text || '').join(' '),
  }));
}

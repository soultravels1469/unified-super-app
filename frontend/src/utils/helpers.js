// Group items by month (YYYY-MM format)
export const groupByMonth = (items) => {
  const grouped = {};
  
  items.forEach(item => {
    if (item.date) {
      const month = item.date.substring(0, 7); // YYYY-MM
      if (!grouped[month]) {
        grouped[month] = [];
      }
      grouped[month].push(item);
    }
  });
  
  // Sort items within each month by date
  Object.keys(grouped).forEach(month => {
    grouped[month].sort((a, b) => new Date(b.date) - new Date(a.date));
  });
  
  return grouped;
};

// Get available months from data
export const getAvailableMonths = (items) => {
  const months = new Set();
  items.forEach(item => {
    if (item.date) {
      months.add(item.date.substring(0, 7));
    }
  });
  return Array.from(months).sort().reverse();
};

// Format month string to readable format
export const formatMonth = (monthStr) => {
  const date = new Date(monthStr + '-01');
  return date.toLocaleDateString('default', { month: 'long', year: 'numeric' });
};

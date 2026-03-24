import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount, showSymbol = true) {
  const formatted = new Intl.NumberFormat('en-NG', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
  return showSymbol ? `₦${formatted}` : formatted;
}

export function formatNumber(num) {
  return new Intl.NumberFormat('en-NG').format(num);
}

export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-NG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatDateTime(dateString) {
  return new Date(dateString).toLocaleString('en-NG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function getStatusColor(status) {
  const normalizedStatus = (status || '').toLowerCase();
  switch (normalizedStatus) {
    case 'pending':
      return 'status-pending';
    case 'approved':
    case 'completed':
      return 'status-approved';
    case 'rejected':
      return 'status-rejected';
    case 'active':
      return 'status-active';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  }
}

export function getInitials(name) {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

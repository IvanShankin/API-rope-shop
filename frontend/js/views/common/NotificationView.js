import { escapeHtml } from '../../utils/text.js?v=20261027.10';
/**
 * Компонент всплывающих уведомлений (Toast)
 */
export class NotificationView {
  static container = null;

  static ensureContainer() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 12px;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
  }

  static show({ title = '', message = '', type = 'info', duration = 4000 }) {
    this.ensureContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.style.cssText = `
      min-width: 280px;
      max-width: 400px;
      background: ${type === 'success' ? '#0F2744' : type === 'error' ? '#3B1212' : '#141E2E'};
      color: #FFFFFF;
      border: 1px solid ${type === 'success' ? '#3A86FF' : type === 'error' ? '#FF4D4D' : '#334E68'};
      border-radius: 8px;
      padding: 14px 18px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.35);
      font-family: 'Manrope', sans-serif;
      font-size: 14px;
      line-height: 1.4;
      pointer-events: auto;
      opacity: 0;
      transform: translateY(12px);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    `;

    toast.innerHTML = `
      ${title ? `<div style="font-weight: 600; margin-bottom: 4px; color: ${type === 'success' ? '#64B5F6' : '#FF8A80'}; font-size: 15px;">${escapeHtml(title)}</div>` : ''}
      <div>${escapeHtml(message)}</div>
    `;

    this.container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  static success(title, message) {
    this.show({ title, message, type: 'success' });
  }

  static error(title, message) {
    this.show({ title, message, type: 'error', duration: 6000 });
  }
}

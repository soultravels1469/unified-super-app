import { NavLink } from 'react-router-dom';
import { LayoutDashboard, DollarSign, Receipt, Clock, FileText, LogOut, Package, Plane, FileCheck, Book, Scale, Wallet, ReceiptText, FileSpreadsheet } from 'lucide-react';

function Layout({ children, onLogout }) {
  const username = localStorage.getItem('username');

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', section: 'main' },
    { to: '/revenue', icon: DollarSign, label: 'Revenue', section: 'main' },
    { to: '/packages', icon: Package, label: 'Tour Packages', section: 'main' },
    { to: '/tickets', icon: Plane, label: 'Tickets', section: 'main' },
    { to: '/visas', icon: FileCheck, label: 'Visas', section: 'main' },
    { to: '/expenses', icon: Receipt, label: 'Expenses', section: 'main' },
    { to: '/pending', icon: Clock, label: 'Pending', section: 'main' },
    { to: '/reports', icon: FileText, label: 'Reports', section: 'main' },
    { to: '/accounting/chart-of-accounts', icon: Book, label: 'Chart of Accounts', section: 'accounting' },
    { to: '/accounting/trial-balance', icon: Scale, label: 'Trial Balance', section: 'accounting' },
    { to: '/accounting/cash-bank', icon: Wallet, label: 'Cash/Bank Book', section: 'accounting' },
    { to: '/accounting/gst', icon: ReceiptText, label: 'GST Summary', section: 'accounting' },
    { to: '/accounting/invoices', icon: FileSpreadsheet, label: 'Invoices', section: 'accounting' },
  ];

  return (
    <div className="layout">
      <aside className="sidebar" data-testid="sidebar">
        <div className="sidebar-header">
          <h2 data-testid="app-title">Soul Immigration</h2>
          <p data-testid="app-subtitle">Finance Dashboard</p>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">Main</div>
            {navItems.filter(item => item.section === 'main').map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
          
          <div className="nav-section">
            <div className="nav-section-title">Accounting</div>
            {navItems.filter(item => item.section === 'accounting').map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                data-testid={`nav-${item.label.toLowerCase().replace(/ /g, '-')}`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info" data-testid="user-info">
            <div className="user-avatar">{username?.[0]?.toUpperCase()}</div>
            <span>{username}</span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onLogout} data-testid="logout-button">
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">{children}</main>

      <style jsx>{`
        .layout {
          display: flex;
          min-height: 100vh;
        }

        .sidebar {
          width: 280px;
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-right: 1px solid rgba(226, 232, 240, 0.8);
          display: flex;
          flex-direction: column;
          position: fixed;
          height: 100vh;
          left: 0;
          top: 0;
          overflow-y: auto;
        }

        .sidebar-header {
          padding: 2rem 1.5rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .sidebar-header h2 {
          font-size: 1.25rem;
          font-weight: 700;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 0.25rem;
        }

        .sidebar-header p {
          font-size: 0.875rem;
          color: #64748b;
        }

        .sidebar-nav {
          flex: 1;
          padding: 1.5rem 0;
          overflow-y: auto;
        }

        .nav-section {
          margin-bottom: 1.5rem;
        }

        .nav-section-title {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #94a3b8;
          padding: 0.5rem 1.5rem;
          margin-bottom: 0.5rem;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          padding: 0.875rem 1.5rem;
          color: #64748b;
          text-decoration: none;
          font-weight: 500;
          transition: all 0.2s ease;
          border-left: 3px solid transparent;
        }

        .nav-item:hover {
          background: #f8fafc;
          color: #6366f1;
        }

        .nav-item.active {
          background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%);
          color: #6366f1;
          border-left-color: #6366f1;
        }

        .sidebar-footer {
          padding: 1.5rem;
          border-top: 1px solid #e2e8f0;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
          color: #475569;
          font-weight: 500;
        }

        .user-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .main-content {
          flex: 1;
          margin-left: 280px;
          background: linear-gradient(135deg, #fef5f7 0%, #f0f4f8 50%, #f5f3ff 100%);
          min-height: 100vh;
        }

        @media (max-width: 768px) {
          .sidebar {
            width: 100%;
            position: relative;
            height: auto;
          }

          .main-content {
            margin-left: 0;
          }

          .layout {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
}

export default Layout;

import React from 'react';

function SidebarLayout({ sidebarCollapsed, sidebar, children }) {
  return (
    <div className={`layout ${sidebarCollapsed ? 'layout--sidebar-collapsed' : ''}`}>
      {sidebar}
      <main className="layout__content">{children}</main>
    </div>
  );
}

export default SidebarLayout;

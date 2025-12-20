import React, { useMemo } from 'react';
import { createPortal } from 'react-dom';

function getOrCreateModalRoot() {
  if (typeof document === 'undefined') return null;

  let root = document.getElementById('modal-root');
  if (!root) {
    root = document.createElement('div');
    root.id = 'modal-root';
    document.body.appendChild(root);
  }
  return root;
}

function ModalPortal({ children }) {
  const modalRoot = useMemo(() => getOrCreateModalRoot(), []);
  if (!modalRoot) return null;
  return createPortal(children, modalRoot);
}

export default ModalPortal;

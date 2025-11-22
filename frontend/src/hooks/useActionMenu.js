import { useState, useEffect, useCallback } from 'react';

export function useActionMenu() {
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuCoords, setMenuCoords] = useState(null);
  const [transferContext, setTransferContext] = useState(null);

  const toggleMenu = useCallback((event, stockId) => {
    event.stopPropagation();

    if (openMenuId === stockId) {
      setOpenMenuId(null);
      setMenuCoords(null);
      setTransferContext(null);
      return;
    }

    setOpenMenuId(stockId);
    setTransferContext(null);

    let triggerEl = event.currentTarget || (event.target && event.target.closest && event.target.closest('.action-menu__trigger')) || event.target || null;
    
    if (!triggerEl || !(triggerEl instanceof Element) || !triggerEl.classList || !triggerEl.classList.contains('action-menu__trigger')) {
      const byAttr = document.querySelector(`.action-menu__trigger[data-stock-id="${stockId}"]`);
      if (byAttr) {
        triggerEl = byAttr;
      } else {
        setMenuCoords({ top: 100, left: 100, width: 320, absolute: false });
        return;
      }
    }

    const rect = triggerEl.getBoundingClientRect();
    const menuWidth = 320;
    const menuHeight = 400;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let finalTop = rect.bottom + 4;
    let finalLeft = rect.left;

    if (finalLeft + menuWidth > viewportWidth) {
      finalLeft = Math.max(8, viewportWidth - menuWidth - 8);
    }

    if (finalTop + menuHeight > viewportHeight) {
      finalTop = Math.max(8, rect.top - menuHeight - 4);
    }

    setMenuCoords({ top: finalTop, left: finalLeft, width: menuWidth, absolute: true });
  }, [openMenuId]);

  const openTransferPanel = useCallback((event, stockId, availableTargets, action) => {
    event.stopPropagation();
    const firstTargetId = availableTargets.length > 0 ? availableTargets[0].id : null;
    setTransferContext({
      stockId,
      action,
      selectedWatchlistId: firstTargetId
    });
  }, []);

  const handleTransferSelectionChange = useCallback((event) => {
    const newId = Number(event.target.value);
    setTransferContext(prev => prev ? { ...prev, selectedWatchlistId: newId } : null);
  }, []);

  const handleCancelTransfer = useCallback((event) => {
    event.stopPropagation();
    setTransferContext(null);
  }, []);

  const handleConfirmTransfer = useCallback((event, stockId, availableTargets) => {
    event.stopPropagation();
    if (!transferContext || !transferContext.selectedWatchlistId) {
      return;
    }

    const targetWatchlist = availableTargets.find(wl => wl.id === transferContext.selectedWatchlistId);
    if (!targetWatchlist) {
      return;
    }

    // This will be handled by parent component via callback
    setOpenMenuId(null);
    setMenuCoords(null);
    setTransferContext(null);
  }, [transferContext]);

  useEffect(() => {
    const closeMenu = () => {
      setOpenMenuId(null);
      setMenuCoords(null);
      setTransferContext(null);
    };

    if (openMenuId !== null) {
      document.addEventListener('click', closeMenu);
      document.addEventListener('scroll', closeMenu, true);
      return () => {
        document.removeEventListener('click', closeMenu);
        document.removeEventListener('scroll', closeMenu, true);
      };
    }
  }, [openMenuId]);

  return {
    openMenuId,
    setOpenMenuId,
    menuCoords,
    setMenuCoords,
    transferContext,
    setTransferContext,
    toggleMenu,
    openTransferPanel,
    handleTransferSelectionChange,
    handleCancelTransfer,
    handleConfirmTransfer
  };
}

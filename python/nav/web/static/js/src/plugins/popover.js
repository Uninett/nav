define([], function () {
  "use strict";

  function init() {
    // Prevent double initialization
    if (document.body.dataset.popoverInitialized) return;
    document.body.dataset.popoverInitialized = "true";

    // Single click handler for all popover interactions
    document.addEventListener('click', handleClick);
    document.addEventListener('popover.open', (e) => {
        const id = e.detail?.id;
        if (!id) return;
        const popover = document.getElementById(id);
        if (popover) openPopover(popover);
    });
    document.addEventListener("popover.close", (e) => {
        const id = e.detail?.id;
        if (!id) return;
        const popover = document.getElementById(id);
        if (popover) closePopover(popover);
    })
  }

  function handleClick(e) {
    // Handle popover triggers
    const trigger = e.target.closest('[data-popover-target]');
    if (trigger) {
      togglePopover(trigger);
      return;
    }

    // Handle close buttons
    const closeButton = e.target.closest('[close-popover]');
    if (closeButton) {
      closePopover(closeButton.closest('.popover'));
      return;
    }

    // Handle outside clicks - close all open popovers
    closeOpenPopovers(e.target);
  }

  function togglePopover(trigger) {
    const target = document.querySelector(trigger.dataset.popoverTarget);
    if (!target) return;

    const isOpen = target.classList.contains('open');

    // Close other popovers first
    closeAllPopovers();

    if (!isOpen) {
      target.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
    } else {
      target.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }
  }

  function openPopover(popover) {
    if (!popover) return;
    const trigger = document.querySelector(`[data-popover-target="#${popover.id}"]`);
    popover.classList.add('open');
    if (trigger) {
      trigger.setAttribute('aria-expanded', 'true');
    }
  }

  function closePopover(popover) {
    if (!popover) return;

    const trigger = document.querySelector(`[data-popover-target="#${popover.id}"]`);
    popover.classList.remove('open');
    if (trigger) {
      trigger.setAttribute('aria-expanded', 'false');
    }
  }

  function closeOpenPopovers(clickTarget) {
    document.querySelectorAll('.popover.open').forEach(popover => {
      const trigger = document.querySelector(`[data-popover-target="#${popover.id}"]`);

      // Don't close if click was inside popover or on trigger
      if (!popover.contains(clickTarget) && !trigger?.contains(clickTarget)) {
        closePopover(popover);
      }
    });
  }

  function closeAllPopovers() {
    document.querySelectorAll('.popover.open').forEach(closePopover);
  }

  init();
});

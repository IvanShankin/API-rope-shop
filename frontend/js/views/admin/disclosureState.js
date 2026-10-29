// Restore only explicitly requested redraws of the current editor.
export function captureDisclosures(root, preserve) {
  return new Map(preserve ? [...root.querySelectorAll('[data-editor-disclosure]')]
    .map(element => [element.dataset.editorDisclosure, element.open]) : []);
}

export function restoreDisclosures(root, state) {
  root.querySelectorAll('[data-editor-disclosure]').forEach(element => {
    if (state.has(element.dataset.editorDisclosure)) element.open = state.get(element.dataset.editorDisclosure);
  });
}

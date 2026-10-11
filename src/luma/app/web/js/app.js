(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const elements = {
    connection: $("#connection-label"),
    category: $("#category-select"),
    preset: $("#preset-select"),
    chooseFolder: $("#choose-folder"),
    addPhotos: $("#add-photos"),
    emptyAddPhotos: $("#empty-add-photos"),
    refreshFolder: $("#refresh-folder"),
    clearPhotos: $("#clear-photos"),
    photoCountChip: $("#photo-count-chip"),
    previewStatus: $("#preview-status"),
    stage: $("#comparison-stage"),
    emptyState: $("#comparison-empty"),
    beforeImage: $("#before-image"),
    afterImage: $("#after-image"),
    afterClip: $("#after-clip"),
    divider: $("#comparison-divider"),
    range: $("#comparison-range"),
    beforeLabel: $("#before-label"),
    afterLabel: $("#after-label"),
    filename: $("#preview-filename"),
    fileFormat: $("#file-format"),
    previewIndex: $("#preview-index"),
    filmstrip: $("#filmstrip"),
    filmstripSubtitle: $("#filmstrip-subtitle"),
    filmstripCount: $("#filmstrip-count"),
    carouselPrev: $("#carousel-prev"),
    carouselNext: $("#carousel-next"),
    activeCategory: $("#active-category"),
    activePresetName: $("#active-preset-name"),
    activePresetDescription: $("#active-preset-description"),
    folderName: $("#folder-name"),
    selectedImageName: $("#selected-image-name"),
    loadedImageCount: $("#loaded-image-count"),
    exportButton: $("#export-photos"),
    exportProgressWrap: $("#export-progress-wrap"),
    exportStatus: $("#export-status"),
    exportPercent: $("#export-percent"),
    exportProgressBar: $("#export-progress-bar"),
    openOutput: $("#open-output"),
    footerMessage: $("#footer-message"),
    toastRegion: $("#toast-region"),
  };

  const state = {
    inputFolder: { name: "Not selected", path: "" },
    photos: [],
    selectedIndex: 0,
    categories: [],
    presets: {},
    selectedPreset: null,
    processing: false,
    lastPreview: null,
  };

  let previewRequestId = 0;
  let statusPollHandle = null;

  const api = () => {
    if (!window.pywebview || !window.pywebview.api) {
      throw new Error("Luma's desktop bridge is not ready yet.");
    }
    return window.pywebview.api;
  };

  async function callApi(method, ...args) {
    const bridge = api();
    if (typeof bridge[method] !== "function") {
      throw new Error(`The Python bridge does not provide "${method}".`);
    }
    return bridge[method](...args);
  }

  function displayName(value) {
    return String(value || "")
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function showToast(message, isError = false) {
    const toast = document.createElement("div");
    toast.className = `toast${isError ? " is-error" : ""}`;
    toast.textContent = message;
    elements.toastRegion.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3600);
  }

  function setConnection(connected, message) {
    elements.connection.textContent = message;
    const dot = document.querySelector(".topbar-center .live-dot");
    if (dot) {
      dot.style.background = connected ? "var(--accent)" : "var(--danger)";
      dot.style.boxShadow = connected ? "0 0 12px rgba(213,255,95,.35)" : "none";
    }
  }

  function setPreviewStatus(message, mode = "") {
    elements.previewStatus.classList.remove("is-rendering", "is-ready");
    if (mode) elements.previewStatus.classList.add(mode);
    elements.previewStatus.innerHTML = "";
    const dot = document.createElement("span");
    dot.className = "status-dot";
    const label = document.createElement("span");
    label.textContent = message;
    elements.previewStatus.append(dot, label);
  }

  function selectedPhoto() {
    return state.photos[state.selectedIndex] || null;
  }

  function currentPreset() {
    for (const category of state.categories) {
      const match = (state.presets[category] || []).find(
        (preset) => preset.name === state.selectedPreset
      );
      if (match) return match;
    }
    return null;
  }

  function inferSelectedCategory() {
    const matchingCategory = state.categories.find((category) =>
      (state.presets[category] || []).some(
        (preset) => preset.name === state.selectedPreset
      )
    );
    return matchingCategory || state.categories[0] || "";
  }

  function setSelectOptions(select, items, valueOf, labelOf, selectedValue) {
    select.replaceChildren();
    for (const item of items) {
      const option = document.createElement("option");
      option.value = valueOf(item);
      option.textContent = labelOf(item);
      select.appendChild(option);
    }
    if (selectedValue != null && [...select.options].some((option) => option.value === selectedValue)) {
      select.value = selectedValue;
    }
    select.disabled = items.length === 0 || state.processing;
  }

  function renderPresetControls() {
    setSelectOptions(
      elements.category,
      state.categories,
      (category) => category,
      (category) => displayName(category),
      inferSelectedCategory()
    );

    const category = elements.category.value;
    const categoryPresets = state.presets[category] || [];
    setSelectOptions(
      elements.preset,
      categoryPresets,
      (preset) => preset.name,
      (preset) => preset.display_name || displayName(preset.name),
      state.selectedPreset
    );

    const active = currentPreset();
    elements.activeCategory.textContent = active
      ? `${displayName(active.category).toUpperCase()} COLLECTION`
      : "PRESET COLLECTION";
    elements.activePresetName.textContent = active
      ? (active.display_name || displayName(active.name))
      : "Choose your look";
    elements.activePresetDescription.textContent = active
      ? "This look is ready to preview. Compare the original and edited image using the slider."
      : "Select a preset to see its effect on your photograph.";
  }

  function renderPhotoDetails() {
    const photo = selectedPhoto();
    const count = state.photos.length;
    elements.photoCountChip.textContent = `${count} ${count === 1 ? "photo" : "photos"}`;
    elements.filmstripCount.textContent = `${String(count).padStart(2, "0")} FRAMES`;
    elements.loadedImageCount.textContent = String(count);
    elements.folderName.textContent = state.inputFolder?.name || "Not selected";
    elements.selectedImageName.textContent = photo?.name || "—";
    elements.filename.textContent = photo ? photo.name.toUpperCase() : "NO IMAGE SELECTED";
    elements.fileFormat.textContent = photo?.name?.includes(".")
      ? photo.name.split(".").pop().toUpperCase()
      : "—";
    elements.previewIndex.textContent = photo
      ? `FRAME ${String(state.selectedIndex + 1).padStart(2, "0")} / ${String(count).padStart(2, "0")}`
      : "FRAME — / —";
    elements.filmstripSubtitle.textContent = state.inputFolder?.path
      ? state.inputFolder.path
      : "Your input folder, all in one place";
    elements.exportButton.disabled = count === 0 || !state.selectedPreset || state.processing;
    elements.clearPhotos.disabled = count === 0 || state.processing;
  }

  function renderFilmstrip() {
    elements.filmstrip.replaceChildren();
    if (!state.photos.length) {
      const empty = document.createElement("div");
      empty.className = "filmstrip-empty";
      empty.textContent = "Your imported images will appear here.";
      elements.filmstrip.appendChild(empty);
      return;
    }

    state.photos.forEach((photo, index) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = `photo-card${index === state.selectedIndex ? " is-selected" : ""}`;
      card.setAttribute("aria-label", `Select photo ${index + 1}: ${photo.name}`);
      card.setAttribute("aria-pressed", index === state.selectedIndex ? "true" : "false");

      const image = document.createElement("img");
      image.className = "photo-thumb";
      image.src = photo.uri;
      image.alt = "";
      image.draggable = false;

      const selectedMark = document.createElement("span");
      selectedMark.className = "photo-selected-mark";
      selectedMark.textContent = "✓";

      const bottom = document.createElement("span");
      bottom.className = "photo-card-bottom";
      const number = document.createElement("span");
      number.className = "photo-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const name = document.createElement("span");
      name.className = "photo-name";
      name.textContent = photo.name;
      bottom.append(number, name);
      card.append(image, selectedMark, bottom);
      card.addEventListener("click", () => choosePhoto(index));
      elements.filmstrip.appendChild(card);
    });

    const selected = elements.filmstrip.querySelector(".photo-card.is-selected");
    if (selected) selected.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
  }

  function setComparisonPosition(value) {
    const clamped = Math.max(0, Math.min(100, Number(value) || 0));
    elements.afterClip.style.clipPath = `inset(0 0 0 ${clamped}%)`;
    elements.divider.style.left = `${clamped}%`;
    elements.range.value = String(clamped);
  }

  function resetComparison() {
    state.lastPreview = null;
    elements.beforeImage.removeAttribute("src");
    elements.afterImage.removeAttribute("src");
    elements.beforeImage.style.display = "none";
    elements.afterClip.style.display = "none";
    elements.divider.style.display = "none";
    elements.range.style.display = "none";
    elements.beforeLabel.style.display = "none";
    elements.afterLabel.style.display = "none";
    elements.emptyState.classList.remove("is-hidden");
    setPreviewStatus(state.photos.length ? "Preparing preview" : "Waiting for a photo");
  }

  async function renderPreview() {
    const photo = selectedPhoto();
    const preset = currentPreset();
    const requestId = ++previewRequestId;

    if (!photo || !preset) {
      resetComparison();
      return;
    }

    elements.emptyState.classList.add("is-hidden");
    elements.beforeImage.style.display = "block";
    elements.afterClip.style.display = "block";
    elements.divider.style.display = "block";
    elements.range.style.display = "block";
    elements.beforeLabel.style.display = "flex";
    elements.afterLabel.style.display = "flex";

    elements.beforeImage.src = photo.uri;
    elements.afterImage.removeAttribute("src");
    setComparisonPosition(elements.range.value || 50);
    setPreviewStatus("Rendering selected look", "is-rendering");

    try {
      const result = await callApi("generate_preview");
      if (requestId !== previewRequestId) return;
      if (!result || !result.success) {
        setPreviewStatus("Preview unavailable");
        showToast(result?.error || "Could not generate the preview.", true);
        return;
      }
      elements.beforeImage.src = result.before || photo.uri;
      elements.afterImage.src = result.after;
      state.lastPreview = result;
      setPreviewStatus("Preview ready", "is-ready");
    } catch (error) {
      if (requestId !== previewRequestId) return;
      setPreviewStatus("Preview unavailable");
      showToast(error.message || "Could not generate the preview.", true);
    }
  }

  async function choosePhoto(index) {
    if (state.processing || index < 0 || index >= state.photos.length) return;
    state.selectedIndex = index;
    try {
      const result = await callApi("select_photo", index);
      if (result?.photos) state.photos = result.photos;
      if (Number.isInteger(result?.selected_index)) state.selectedIndex = result.selected_index;
      renderFilmstrip();
      renderPhotoDetails();
      await renderPreview();
    } catch (error) {
      showToast(error.message || "Could not select that photo.", true);
    }
  }

  async function changePreset(presetName) {
    if (!presetName || state.processing) return;
    try {
      const result = await callApi("select_preset", presetName);
      if (!result?.success) throw new Error(result?.error || "Could not select preset.");
      state.selectedPreset = result.preset?.name || presetName;
      renderPresetControls();
      renderPhotoDetails();
      await renderPreview();
    } catch (error) {
      showToast(error.message || "Could not select that preset.", true);
    }
  }

  async function handleCategoryChange() {
    const category = elements.category.value;
    const options = state.presets[category] || [];
    if (!options.length) {
      state.selectedPreset = null;
      renderPresetControls();
      renderPhotoDetails();
      resetComparison();
      return;
    }
    await changePreset(options[0].name);
  }

  function hydrateFromInitialState(initial) {
    state.inputFolder = initial.input_folder || state.inputFolder;
    state.photos = Array.isArray(initial.photos) ? initial.photos : [];
    state.selectedIndex = Number.isInteger(initial.selected_index) ? initial.selected_index : 0;
    state.categories = Array.isArray(initial.categories) ? initial.categories : [];
    state.presets = initial.presets || {};
    state.selectedPreset = initial.selected_preset || null;

    if (initial.processing) updateProcessingUI(initial.processing);
    renderPresetControls();
    renderFilmstrip();
    renderPhotoDetails();

    if (state.photos.length && state.selectedPreset) {
      renderPreview();
    } else {
      resetComparison();
    }
  }

  async function initialise() {
    try {
      setConnection(true, "Connected to Luma engine");
      const initial = await callApi("get_initial_state");
      hydrateFromInitialState(initial);
      if (initial.input_folder?.path) {
        elements.footerMessage.textContent = "Your images stay on your machine.";
      }
      showToast("Luma is ready. Choose a look and start editing.");
      startStatusPolling();
    } catch (error) {
      setConnection(false, "Could not connect to Luma engine");
      showToast(error.message || "Could not initialise Luma.", true);
    }
  }

  async function chooseFolder() {
    if (state.processing) return;
    try {
      const result = await callApi("select_folder");
      if (!result) return;
      state.inputFolder = { name: result.name, path: result.path };
      state.photos = result.photos || [];
      state.selectedIndex = 0;
      renderFilmstrip();
      renderPhotoDetails();
      if (state.photos.length) {
        await renderPreview();
      } else {
        resetComparison();
        showToast("Folder selected. No supported images were found.");
      }
    } catch (error) {
      showToast(error.message || "Could not select that folder.", true);
    }
  }

  async function addPhotos() {
    if (state.processing) return;
    try {
      const result = await callApi("select_images");
      if (!result) return;
      state.photos = result.photos || [];
      state.selectedIndex = Number.isInteger(result.selected_index) ? result.selected_index : 0;
      renderFilmstrip();
      renderPhotoDetails();
      if (state.photos.length) await renderPreview();
    } catch (error) {
      showToast(error.message || "Could not add photos.", true);
    }
  }

  async function refreshFolder() {
    if (state.processing) return;
    try {
      await callApi("sync_input_folder");
      const initial = await callApi("get_initial_state");
      hydrateFromInitialState(initial);
      showToast("Input folder refreshed.");
    } catch (error) {
      showToast(error.message || "Could not refresh the input folder.", true);
    }
  }

  async function clearPhotos() {
    if (state.processing) return;
    try {
      const result = await callApi("clear_photos");
      state.photos = result?.photos || [];
      state.selectedIndex = result?.selected_index || 0;
      renderFilmstrip();
      renderPhotoDetails();
      resetComparison();
      showToast("Photo selection cleared.");
    } catch (error) {
      showToast(error.message || "Could not clear photos.", true);
    }
  }

  function updateProcessingUI(status = {}) {
    const isProcessing = Boolean(status.processing);
    state.processing = isProcessing;

    elements.exportButton.disabled = isProcessing || state.photos.length === 0 || !state.selectedPreset;
    elements.exportButton.querySelector("span").textContent = isProcessing ? "Exporting photos…" : "Export photos";
    elements.chooseFolder.disabled = isProcessing;
    elements.addPhotos.disabled = isProcessing;
    elements.refreshFolder.disabled = isProcessing;
    elements.clearPhotos.disabled = isProcessing || state.photos.length === 0;
    elements.category.disabled = isProcessing || state.categories.length === 0;
    elements.preset.disabled = isProcessing || !currentPreset();

    if (isProcessing || (status.total && status.progress != null && status.progress >= 1)) {
      elements.exportProgressWrap.hidden = false;
    } else if (!status.status || status.status === "Ready") {
      elements.exportProgressWrap.hidden = true;
    }

    const progress = Math.max(0, Math.min(1, Number(status.progress) || 0));
    elements.exportProgressBar.style.width = `${Math.round(progress * 100)}%`;
    elements.exportPercent.textContent = `${Math.round(progress * 100)}%`;
    elements.exportStatus.textContent = status.status || (isProcessing ? "Exporting photos…" : "Ready");
    if (!isProcessing && status.total && progress >= 1) {
      elements.exportButton.querySelector("span").textContent = "Export complete";
    }
  }

  async function exportPhotos() {
    if (state.processing || !state.photos.length || !state.selectedPreset) return;
    try {
      const result = await callApi("process_photos");
      if (!result?.success) throw new Error(result?.error || "Could not start export.");
      elements.exportProgressWrap.hidden = false;
      elements.exportButton.querySelector("span").textContent = "Exporting photos…";
      showToast("Export started. You can follow its progress here.");
      startStatusPolling(true);
    } catch (error) {
      showToast(error.message || "Could not start export.", true);
    }
  }

  async function pollProcessingStatus() {
    try {
      const status = await callApi("get_processing_status");
      if (!status) return;
      const wasProcessing = state.processing;
      updateProcessingUI(status);
      if (wasProcessing && !status.processing) {
        renderPhotoDetails();
        if (status.failed > 0) {
          showToast(`Export finished: ${status.successful} succeeded, ${status.failed} failed.`, true);
        } else if (status.total) {
          showToast(`Export complete — ${status.successful} ${status.successful === 1 ? "photo" : "photos"} saved.`);
        }
      }
    } catch (_) {
      // A transient bridge hiccup shouldn't interrupt the UI.
    }
  }

  function startStatusPolling(immediate = false) {
    if (statusPollHandle) window.clearInterval(statusPollHandle);
    if (immediate) pollProcessingStatus();
    statusPollHandle = window.setInterval(pollProcessingStatus, 700);
  }

  async function openOutputFolder() {
    try {
      const result = await callApi("open_output_folder");
      if (!result?.success) throw new Error(result?.error || "Could not open export folder.");
      showToast("Opening export folder.");
    } catch (error) {
      showToast(error.message || "Could not open export folder.", true);
    }
  }

  function bindEvents() {
    elements.category.addEventListener("change", handleCategoryChange);
    elements.preset.addEventListener("change", () => changePreset(elements.preset.value));
    elements.chooseFolder.addEventListener("click", chooseFolder);
    elements.addPhotos.addEventListener("click", addPhotos);
    elements.emptyAddPhotos.addEventListener("click", addPhotos);
    elements.refreshFolder.addEventListener("click", refreshFolder);
    elements.clearPhotos.addEventListener("click", clearPhotos);
    elements.exportButton.addEventListener("click", exportPhotos);
    elements.openOutput.addEventListener("click", openOutputFolder);

    elements.range.addEventListener("input", () => setComparisonPosition(elements.range.value));
    elements.carouselPrev.addEventListener("click", () => elements.filmstrip.scrollBy({ left: -330, behavior: "smooth" }));
    elements.carouselNext.addEventListener("click", () => elements.filmstrip.scrollBy({ left: 330, behavior: "smooth" }));

    elements.filmstrip.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") {
        event.preventDefault();
        choosePhoto(Math.min(state.photos.length - 1, state.selectedIndex + 1));
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        choosePhoto(Math.max(0, state.selectedIndex - 1));
      }
    });

    // PyWebView can expose native dropped paths on supported platforms.
    elements.stage.addEventListener("dragover", (event) => {
      event.preventDefault();
      elements.stage.classList.add("is-dragging");
    });
    elements.stage.addEventListener("dragleave", () => elements.stage.classList.remove("is-dragging"));
    elements.stage.addEventListener("drop", async (event) => {
      event.preventDefault();
      elements.stage.classList.remove("is-dragging");
      const paths = [...(event.dataTransfer?.files || [])]
        .map((file) => file.path)
        .filter(Boolean);
      if (!paths.length) {
        showToast("Use “Add photos” or “Input folder” to import images.");
        return;
      }
      try {
        const result = await callApi("add_dropped_paths", paths);
        state.photos = result?.photos || [];
        state.selectedIndex = Number.isInteger(result?.selected_index) ? result.selected_index : 0;
        renderFilmstrip();
        renderPhotoDetails();
        if (state.photos.length) await renderPreview();
      } catch (error) {
        showToast(error.message || "Could not import dropped files.", true);
      }
    });
  }

  bindEvents();
  setComparisonPosition(50);

  if (window.pywebview && window.pywebview.api) {
    initialise();
  } else {
    window.addEventListener("pywebviewready", initialise, { once: true });
    // If opened in a normal browser, keep the UI informative rather than failing silently.
    window.setTimeout(() => {
      if (!(window.pywebview && window.pywebview.api)) {
        setConnection(false, "Open this window from the Luma desktop app");
      }
    }, 1600);
  }
})();

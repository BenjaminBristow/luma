let photos = [];
let selectedIndex = 0;

let categories = [];
let presets = {};
let selectedPreset = null;

let carouselPosition = 0;
let carouselTarget = 0;

let carouselDragging = false;
let carouselDragStartX = 0;
let carouselDragStartPosition = 0;

let hoveredIndex = null;

let previewDragging = false;
let previewDivider = 0.5;

let lastFolderSignature = "";
let processing = false;


/* ---------------------------------------------------------
   DOM
--------------------------------------------------------- */

const carousel =
    document.getElementById("carousel");

const carouselTrack =
    document.getElementById("carousel-track");

const preview =
    document.getElementById("preview");

const beforeImage =
    document.getElementById("before-image");

const afterImage =
    document.getElementById("after-image");

const afterContainer =
    document.getElementById("after-container");

const divider =
    document.getElementById("preview-divider");

const previewEmpty =
    document.getElementById("preview-empty");

const categorySelect =
    document.getElementById("category-select");

const presetList =
    document.getElementById("preset-list");

const statusElement =
    document.getElementById("status");

const progress =
    document.getElementById("progress");


/* ---------------------------------------------------------
   Startup
--------------------------------------------------------- */

window.addEventListener("pywebviewready", async () => {

    try {

        const state =
            await pywebview.api.get_initial_state();

        applyInitialState(state);

        startFolderWatcher();

        startProcessingWatcher();

    } catch (error) {

        console.error(error);

        setStatus(
            "Failed to initialise Luma",
            "error"
        );
    }

});


/* ---------------------------------------------------------
   Initial state
--------------------------------------------------------- */

function applyInitialState(state) {

    updateFolder(
        state.input_folder
    );

    categories =
        state.categories || [];

    presets =
        state.presets || {};

    selectedPreset =
        state.selected_preset;

    photos =
        state.photos || [];

    selectedIndex =
        state.selected_index || 0;

    populateCategories();

    renderPresets();

    renderCarousel();

    updatePhotoInformation();

    if (photos.length > 0) {

        selectPhoto(
            selectedIndex,
            false
        );

    }
}


/* ---------------------------------------------------------
   Folder
--------------------------------------------------------- */

function updateFolder(folder) {

    if (!folder) {
        return;
    }

    document.getElementById(
        "input-folder-name"
    ).textContent = folder.name;

    document.getElementById(
        "input-folder-path"
    ).textContent = folder.path;
}


document
    .getElementById("change-folder-button")
    .addEventListener(
        "click",
        async () => {

            const result =
                await pywebview.api.select_folder();

            if (!result) {
                return;
            }

            updateFolder(result);

            photos =
                result.photos || [];

            selectedIndex = 0;

            carouselPosition = 0;
            carouselTarget = 0;

            renderCarousel();

            updatePhotoInformation();

            if (photos.length > 0) {
                await selectPhoto(
                    0,
                    false
                );
            } else {
                clearPreview();
            }

        }
    );


/* ---------------------------------------------------------
   Add photos
--------------------------------------------------------- */

document
    .getElementById("add-photos-button")
    .addEventListener(
        "click",
        async () => {

            const state =
                await pywebview.api.select_images();

            applyPhotoState(state);

            if (photos.length > 0) {
                await generatePreview();
            }

        }
    );


/* ---------------------------------------------------------
   Photo state
--------------------------------------------------------- */

function applyPhotoState(state) {

    if (!state) {
        return;
    }

    photos =
        state.photos || [];

    selectedIndex =
        state.selected_index || 0;

    if (
        selectedIndex >= photos.length
    ) {
        selectedIndex = 0;
    }

    carouselPosition =
        selectedIndex;

    carouselTarget =
        selectedIndex;

    renderCarousel();

    updatePhotoInformation();
}


function updatePhotoInformation() {

    const count =
        photos.length;

    document.getElementById(
        "photo-count"
    ).textContent =
        `${count} photo${count === 1 ? "" : "s"}`;

    if (!photos.length) {

        document.getElementById(
            "selected-photo-label"
        ).textContent =
            "No photos";

        return;
    }

    document.getElementById(
        "selected-photo-label"
    ).textContent =
        `Photo ${selectedIndex + 1} of ${photos.length} • ${photos[selectedIndex].name}`;
}


/* ---------------------------------------------------------
   Clear
--------------------------------------------------------- */

document
    .getElementById("clear-button")
    .addEventListener(
        "click",
        async () => {

            if (processing) {
                return;
            }

            const state =
                await pywebview.api.clear_photos();

            applyPhotoState(state);

            clearPreview();

            setStatus(
                "Ready — folder is still being watched"
            );
        }
    );


/* ---------------------------------------------------------
   Carousel
--------------------------------------------------------- */

function renderCarousel() {

    carouselTrack.innerHTML = "";

    if (!photos.length) {
        return;
    }

    photos.forEach(
        (photo, index) => {

            const item =
                document.createElement("div");

            item.className =
                "carousel-item";

            item.dataset.index =
                index;

            const image =
                document.createElement("img");

            image.src =
                photo.uri;

            image.draggable = false;

            item.appendChild(image);

            item.addEventListener(
                "click",
                () => {
                    selectPhoto(index, true);
                }
            );

            item.addEventListener(
                "mouseenter",
                () => {
                    hoveredIndex = index;
                    updateCarouselVisuals();
                }
            );

            item.addEventListener(
                "mouseleave",
                () => {
                    hoveredIndex = null;
                    updateCarouselVisuals();
                }
            );

            carouselTrack.appendChild(item);
        }
    );

    updateCarouselVisuals();
}


function updateCarouselVisuals() {

    const items =
        Array.from(
            carouselTrack.children
        );

    const maxDistance = 4.5;

    items.forEach(
        (item, index) => {

            const distance =
                index - carouselPosition;

            const absolute =
                Math.abs(distance);

            if (
                absolute > maxDistance
            ) {

                item.style.opacity = "0";
                item.style.pointerEvents =
                    "none";

                return;
            }

            const t =
                Math.min(
                    1,
                    absolute / maxDistance
                );

            const smooth =
                t * t * (3 - 2 * t);

            const scale =
                1 - 0.48 * smooth;

            const opacity =
                1 - 0.82 * smooth;

            const x =
                distance * 125;

            item.style.transform =
                `translateX(${x}px) translateY(-50%) scale(${scale})`;

            item.style.opacity =
                opacity;

            item.style.pointerEvents =
                opacity > 0.05
                    ? "auto"
                    : "none";

            item.classList.toggle(
                "selected",
                index === selectedIndex
            );

            item.classList.toggle(
                "hovered",
                index === hoveredIndex
            );
        }
    );

}


function moveCarousel(direction) {

    if (!photos.length) {
        return;
    }

    let destination =
        Math.round(carouselTarget)
        + direction;

    destination =
        Math.max(
            0,
            Math.min(
                photos.length - 1,
                destination
            )
        );

    selectPhoto(
        destination,
        true
    );
}


document
    .getElementById("carousel-left")
    .addEventListener(
        "click",
        () => moveCarousel(-1)
    );


document
    .getElementById("carousel-right")
    .addEventListener(
        "click",
        () => moveCarousel(1)
    );


/* ---------------------------------------------------------
   Carousel animation
--------------------------------------------------------- */

function animateCarousel() {

    const difference =
        carouselTarget - carouselPosition;

    if (Math.abs(difference) < 0.01) {

        carouselPosition =
            carouselTarget;

        updateCarouselVisuals();

        return;
    }

    carouselPosition +=
        difference * 0.18;

    updateCarouselVisuals();

    requestAnimationFrame(
        animateCarousel
    );
}


/* ---------------------------------------------------------
   Select photo
--------------------------------------------------------- */

async function selectPhoto(
    index,
    animate = true
) {

    if (!photos.length) {
        return;
    }

    index =
        Math.max(
            0,
            Math.min(
                photos.length - 1,
                index
            )
        );

    selectedIndex = index;

    carouselTarget = index;

    if (!animate) {
        carouselPosition = index;
    } else {
        requestAnimationFrame(
            animateCarousel
        );
    }

    updatePhotoInformation();

    const state =
        await pywebview.api.select_photo(
            index
        );

    if (state) {
        photos =
            state.photos || photos;
    }

    renderCarousel();

    await generatePreview();
}


/* ---------------------------------------------------------
   Carousel wheel / trackpad
--------------------------------------------------------- */

carousel.addEventListener(
    "wheel",
    event => {

        if (!photos.length) {
            return;
        }

        event.preventDefault();

        let movement;

        if (
            Math.abs(event.deltaX)
            > Math.abs(event.deltaY)
        ) {
            movement =
                event.deltaX / 300;
        } else {
            movement =
                event.deltaY / 300;
        }

        carouselTarget =
            Math.max(
                0,
                Math.min(
                    photos.length - 1,
                    carouselTarget + movement
                )
            );

        requestAnimationFrame(
            animateCarousel
        );

        const nearest =
            Math.round(carouselTarget);

        if (
            nearest !== selectedIndex
        ) {
            selectPhoto(
                nearest,
                false
            );
        }

    },
    {
        passive: false
    }
);


/* ---------------------------------------------------------
   Carousel dragging
--------------------------------------------------------- */

carousel.addEventListener(
    "pointerdown",
    event => {

        if (!photos.length) {
            return;
        }

        carouselDragging = true;

        carouselDragStartX =
            event.clientX;

        carouselDragStartPosition =
            carouselPosition;

        carousel.setPointerCapture(
            event.pointerId
        );
    }
);


carousel.addEventListener(
    "pointermove",
    event => {

        if (!carouselDragging) {
            return;
        }

        const dx =
            event.clientX
            - carouselDragStartX;

        const position =
            carouselDragStartPosition
            - dx / 125;

        carouselPosition =
            Math.max(
                0,
                Math.min(
                    photos.length - 1,
                    position
                )
            );

        carouselTarget =
            carouselPosition;

        const nearest =
            Math.round(
                carouselPosition
            );

        if (
            nearest !== selectedIndex
        ) {

            selectedIndex =
                nearest;

            updatePhotoInformation();
        }

        updateCarouselVisuals();
    }
);


carousel.addEventListener(
    "pointerup",
    event => {

        if (!carouselDragging) {
            return;
        }

        carouselDragging = false;

        try {
            carousel.releasePointerCapture(
                event.pointerId
            );
        } catch (_) {}

        const nearest =
            Math.round(
                carouselPosition
            );

        selectPhoto(
            nearest,
            true
        );
    }
);


/* ---------------------------------------------------------
   Keyboard
--------------------------------------------------------- */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "ArrowLeft"
        ) {

            moveCarousel(-1);

            event.preventDefault();

        } else if (
            event.key === "ArrowRight"
        ) {

            moveCarousel(1);

            event.preventDefault();
        }
    }
);


/* ---------------------------------------------------------
   Presets
--------------------------------------------------------- */

function populateCategories() {

    categorySelect.innerHTML = "";

    categories.forEach(
        category => {

            const option =
                document.createElement("option");

            option.value =
                category;

            option.textContent =
                displayName(category);

            categorySelect.appendChild(
                option
            );
        }
    );

    if (categories.length) {
        categorySelect.value =
            categories[0];
    }
}


categorySelect.addEventListener(
    "change",
    () => {
        renderPresets();
    }
);


function renderPresets() {

    presetList.innerHTML = "";

    const category =
        categorySelect.value;

    const categoryPresets =
        presets[category] || [];

    categoryPresets.forEach(
        preset => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "preset-card";

            if (
                preset.name ===
                selectedPreset
            ) {
                card.classList.add(
                    "selected"
                );
            }

            const checkbox =
                document.createElement(
                    "input"
                );

            checkbox.type =
                "checkbox";

            checkbox.checked =
                preset.name ===
                selectedPreset;

            const content =
                document.createElement(
                    "div"
                );

            const title =
                document.createElement(
                    "div"
                );

            title.textContent =
                preset.display_name;

            const description =
                document.createElement(
                    "div"
                );

            description.textContent =
                `${displayName(preset.category)} preset`;

            content.appendChild(title);
            content.appendChild(description);

            card.appendChild(
                checkbox
            );

            card.appendChild(
                content
            );

            card.addEventListener(
                "click",
                async event => {

                    if (
                        event.target ===
                        checkbox
                    ) {
                        return;
                    }

                    await choosePreset(
                        preset.name
                    );
                }
            );

            checkbox.addEventListener(
                "change",
                async () => {

                    if (
                        checkbox.checked
                    ) {

                        await choosePreset(
                            preset.name
                        );

                    } else {

                        checkbox.checked =
                            true;
                    }
                }
            );

            presetList.appendChild(
                card
            );
        }
    );
}


async function choosePreset(
    name
) {

    const result =
        await pywebview.api.select_preset(
            name
        );

    if (!result.success) {

        setStatus(
            result.error,
            "error"
        );

        return;
    }

    selectedPreset =
        name;

    renderPresets();

    await generatePreview();
}


/* ---------------------------------------------------------
   Preview
--------------------------------------------------------- */

async function generatePreview() {

    if (!photos.length) {
        clearPreview();
        return;
    }

    if (!selectedPreset) {
        return;
    }

    setStatus(
        "Generating preview..."
    );

    const result =
        await pywebview.api.generate_preview();

    if (!result.success) {

        setStatus(
            result.error,
            "error"
        );

        return;
    }

    beforeImage.src =
        result.before;

    afterImage.src =
        result.after;

    beforeImage.style.display =
        "block";

    afterImage.style.display =
        "block";

    afterContainer.style.display =
        "block";

    previewEmpty.style.display =
        "none";

    updatePreviewDivider();

    setStatus(
        "Ready"
    );
}


function clearPreview() {

    beforeImage.removeAttribute(
        "src"
    );

    afterImage.removeAttribute(
        "src"
    );

    beforeImage.style.display =
        "none";

    afterImage.style.display =
        "none";

    afterContainer.style.display =
        "none";

    previewEmpty.style.display =
        "flex";
}


/* ---------------------------------------------------------
   Before / after slider
--------------------------------------------------------- */

function updatePreviewDivider() {

    const width =
        preview.clientWidth;

    const x =
        width * previewDivider;

    afterContainer.style.width =
        `${x}px`;

    divider.style.left =
        `${x}px`;
}


function setPreviewDivider(
    clientX
) {

    const rect =
        preview.getBoundingClientRect();

    let percentage =
        (clientX - rect.left)
        / rect.width;

    percentage =
        Math.max(
            0,
            Math.min(
                1,
                percentage
            )
        );

    previewDivider =
        percentage;

    updatePreviewDivider();
}


preview.addEventListener(
    "pointerdown",
    event => {

        if (
            beforeImage.style.display ===
            "none"
        ) {
            return;
        }

        previewDragging = true;

        preview.setPointerCapture(
            event.pointerId
        );

        setPreviewDivider(
            event.clientX
        );
    }
);


preview.addEventListener(
    "pointermove",
    event => {

        if (!previewDragging) {
            return;
        }

        setPreviewDivider(
            event.clientX
        );
    }
);


preview.addEventListener(
    "pointerup",
    event => {

        previewDragging = false;

        try {
            preview.releasePointerCapture(
                event.pointerId
            );
        } catch (_) {}
    }
);


window.addEventListener(
    "resize",
    updatePreviewDivider
);


/* ---------------------------------------------------------
   Folder watcher
--------------------------------------------------------- */

function startFolderWatcher() {

    setInterval(
        async () => {

            if (processing) {
                return;
            }

            try {

                const folderImages =
                    await pywebview.api.get_folder_images();

                const signature =
                    JSON.stringify(
                        folderImages.map(
                            photo => photo.path
                        )
                    );

                if (
                    signature !==
                    lastFolderSignature
                ) {

                    lastFolderSignature =
                        signature;

                    const externalPhotos =
                        photos.filter(
                            photo => {

                                return !photo.path.startsWith(
                                    document
                                        .getElementById(
                                            "input-folder-path"
                                        )
                                        .textContent
                                );
                            }
                        );

                    photos =
                        folderImages.concat(
                            externalPhotos
                        );

                    if (
                        selectedIndex >=
                        photos.length
                    ) {
                        selectedIndex = 0;
                    }

                    renderCarousel();

                    updatePhotoInformation();

                }

            } catch (error) {

                console.error(
                    "Folder watcher error:",
                    error
                );
            }

        },
        750
    );
}


/* ---------------------------------------------------------
   Processing
--------------------------------------------------------- */

document
    .getElementById("edit-button")
    .addEventListener(
        "click",
        async () => {

            if (processing) {
                return;
            }

            const result =
                await pywebview.api.process_photos();

            if (!result.success) {

                setStatus(
                    result.error,
                    "error"
                );

                return;
            }

            processing = true;

            document
                .getElementById(
                    "edit-button"
                )
                .disabled = true;

            setStatus(
                "Preparing photos..."
            );
        }
    );


function startProcessingWatcher() {

    setInterval(
        async () => {

            try {

                const state =
                    await pywebview.api.get_processing_status();

                if (
                    !state
                ) {
                    return;
                }

                processing =
                    state.processing;

                progress.style.width =
                    `${state.progress * 100}%`;

                if (
                    state.processing
                ) {

                    setStatus(
                        state.status
                    );

                } else if (
                    state.progress === 1
                    && state.total > 0
                ) {

                    setStatus(
                        state.status,
                        state.failed > 0
                            ? "error"
                            : "success"
                    );

                    document
                        .getElementById(
                            "edit-button"
                        )
                        .disabled = false;
                }

            } catch (error) {

                console.error(
                    "Processing watcher error:",
                    error
                );
            }

        },
        250
    );
}


/* ---------------------------------------------------------
   Output
--------------------------------------------------------- */

document
    .getElementById(
        "open-output-button"
    )
    .addEventListener(
        "click",
        async () => {

            const result =
                await pywebview.api.open_output_folder();

            if (
                !result.success
            ) {

                setStatus(
                    result.error,
                    "error"
                );
            }
        }
    );


/* ---------------------------------------------------------
   Utility
--------------------------------------------------------- */

function displayName(
    value
) {

    return value
        .replaceAll("-", " ")
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}


function setStatus(
    message,
    type = ""
) {

    statusElement.textContent =
        message;

    statusElement.className =
        type;
}


/* ---------------------------------------------------------
   Window drag/drop
--------------------------------------------------------- */

document.addEventListener(
    "dragover",
    event => {
        event.preventDefault();
    }
);


document.addEventListener(
    "drop",
    async event => {

        event.preventDefault();

        const files =
            Array.from(
                event.dataTransfer.files
            );

        const paths =
            files
                .map(
                    file => file.path
                )
                .filter(Boolean);

        if (!paths.length) {
            return;
        }

        const state =
            await pywebview.api.add_dropped_paths(
                paths
            );

        applyPhotoState(state);

        if (photos.length) {
            await generatePreview();
        }
    }
);

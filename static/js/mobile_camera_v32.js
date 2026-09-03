document.addEventListener("DOMContentLoaded", () => {
  const forms = [...document.querySelectorAll(".m32-camera-form")];

  function setError(form, message) {
    const el = form.querySelector(".m32-camera-error");
    if (!el) return;
    el.textContent = message || "";
    el.hidden = !message;
  }

  function stopStream(form) {
    const video = form.querySelector(".m32-camera-video");
    const stream = video && video.srcObject;
    if (stream && stream.getTracks) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (video) video.srcObject = null;
  }

  function showStage(form) {
    form.querySelector(".m32-open-camera").hidden = true;
    form.querySelector(".m32-camera-result").hidden = true;
    form.querySelector(".m32-camera-stage").hidden = false;
  }

  function showReady(form, url) {
    const preview = form.querySelector(".m32-camera-preview");
    if (preview) preview.src = url;
    form.querySelector(".m32-camera-stage").hidden = true;
    form.querySelector(".m32-open-camera").hidden = true;
    form.querySelector(".m32-camera-result").hidden = false;
    form.dataset.photoReady = "1";
    setError(form, "");
  }

  function fallbackCamera(form) {
    const input = form.querySelector(".m32-camera-file");
    if (!input) return;
    setError(form, "");
    input.click();
  }

  async function openCamera(form) {
    setError(form, "");
    const video = form.querySelector(".m32-camera-video");

    // getUserMedia; ilk kullanımda tarayıcı/Android kamera iznini sorar.
    // İzin site/uygulama için hatırlandığında sonraki açılışlarda yeniden sormaz.
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });
        video.srcObject = stream;
        showStage(form);
        try { await video.play(); } catch (_) {}
        return;
      } catch (err) {
        if (err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")) {
          setError(form, "Kamera izni verilmedi. Tarayıcı veya uygulama ayarlarından kamera iznini açın.");
          return;
        }
        // Yerel ağda HTTP gibi getUserMedia desteklenmeyen durumlarda
        // capture=environment kullanan gizli input doğrudan kamera uygulamasını açar.
        fallbackCamera(form);
        return;
      }
    }

    fallbackCamera(form);
  }

  async function capture(form) {
    const video = form.querySelector(".m32-camera-video");
    const input = form.querySelector(".m32-camera-file");
    if (!video || !input || !video.videoWidth || !video.videoHeight) {
      setError(form, "Kamera görüntüsü henüz hazır değil. Bir saniye sonra tekrar deneyin.");
      return;
    }

    const maxWidth = 1600;
    const scale = Math.min(1, maxWidth / video.videoWidth);
    const width = Math.max(1, Math.round(video.videoWidth * scale));
    const height = Math.max(1, Math.round(video.videoHeight * scale));

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.86));
    if (!blob) {
      setError(form, "Fotoğraf oluşturulamadı. Yeniden deneyin.");
      return;
    }

    const field = form.dataset.cameraField || "saha_foto";
    const file = new File(
      [blob],
      `${field}_${Date.now()}.jpg`,
      { type: "image/jpeg", lastModified: Date.now() }
    );

    try {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    } catch (_) {
      // DataTransfer olmayan eski tarayıcıda doğrudan kamera inputuna dön.
      stopStream(form);
      fallbackCamera(form);
      return;
    }

    const previewUrl = URL.createObjectURL(blob);
    stopStream(form);
    showReady(form, previewUrl);
  }

  forms.forEach(form => {
    const open = form.querySelector(".m32-open-camera");
    const captureButton = form.querySelector(".m32-capture");
    const cancel = form.querySelector(".m32-cancel-camera");
    const retake = form.querySelector(".m32-retake");
    const fileInput = form.querySelector(".m32-camera-file");

    open?.addEventListener("click", () => openCamera(form));
    captureButton?.addEventListener("click", () => capture(form));

    cancel?.addEventListener("click", () => {
      stopStream(form);
      form.querySelector(".m32-camera-stage").hidden = true;
      open.hidden = false;
    });

    retake?.addEventListener("click", () => {
      stopStream(form);
      fileInput.value = "";
      form.dataset.photoReady = "0";
      form.querySelector(".m32-camera-result").hidden = true;
      open.hidden = false;
      openCamera(form);
    });

    // Fallback capture input sonucu da aynı sade önizlemeye çevrilir.
    fileInput?.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        fileInput.value = "";
        setError(form, "Yalnızca fotoğraf kullanılabilir.");
        return;
      }
      if (file.size > 8 * 1024 * 1024) {
        fileInput.value = "";
        setError(form, "Fotoğraf en fazla 8 MB olabilir.");
        return;
      }
      showReady(form, URL.createObjectURL(file));
    });

    form.addEventListener("submit", event => {
      const file = fileInput?.files?.[0];
      if (!file) {
        event.preventDefault();
        setError(form, "Devam etmek için fotoğraf çekin.");
        openCamera(form);
      }
    });
  });

  window.addEventListener("pagehide", () => forms.forEach(stopStream));
});
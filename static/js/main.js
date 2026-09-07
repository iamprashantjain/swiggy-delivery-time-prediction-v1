document.getElementById('predictionForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const form = e.target;
  const submitBtn = document.getElementById('submitBtn');
  const loader = document.getElementById('loader');
  const btnText = submitBtn.querySelector('.btn-text');
  const resultContainer = document.getElementById('resultContainer');
  const placeholderView = document.getElementById('placeholderView');
  const predictionResult = document.getElementById('predictionResult');

  // Show loading state
  submitBtn.style.pointerEvents = 'none';
  btnText.style.opacity = '0.3';
  loader.style.display = 'block';

  // Extract and Convert Data
  const formData = new FormData(form);
  const data = {};
  formData.forEach((value, key) => {
    // Numeric conversion for coordinates and specific metrics
    if (['Restaurant_latitude', 'Restaurant_longitude',
      'Delivery_location_latitude', 'Delivery_location_longitude',
      'Delivery_person_Age', 'Delivery_person_Ratings',
      'multiple_deliveries'].includes(key)) {
      data[key] = parseFloat(value);
    } else if (key === 'Vehicle_condition') {
      data[key] = parseInt(value);
    } else {
      data[key] = value;
    }
  });

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) throw new Error('API_ERROR');

    const result = await response.json();

    // UI Transition
    placeholderView.style.display = 'none';
    resultContainer.style.display = 'block';

    // Premium Counter Animation
    const targetValue = Math.round(result);
    animateValue(predictionResult, 0, targetValue, 1200);

    // Sync with Header Output
    const headerValue = document.getElementById('headerValue');
    animateValue(headerValue, 0, targetValue, 1200);

    // Success Haptic Feedback (visual)
    submitBtn.style.background = '#2ecc71';
    setTimeout(() => {
      submitBtn.style.background = 'var(--primary)';
    }, 1000);

  } catch (error) {
    console.error('Core Engine Error:', error);
    alert('Critical Engine Error: Please verify input telemetry data.');
  } finally {
    submitBtn.style.pointerEvents = 'auto';
    btnText.style.opacity = '1';
    loader.style.display = 'none';
  }
});

/**
 * Precision Counter Animation
 */
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);

    // Easing function: outExpo
    const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

    const currentVal = Math.floor(easeProgress * (end - start) + start);
    obj.innerHTML = currentVal < 10 ? `0${currentVal}` : currentVal;

    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

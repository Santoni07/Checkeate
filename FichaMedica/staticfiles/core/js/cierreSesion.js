function checkSession() {
    fetch('/account/check_session/', {
      method: 'GET',
      credentials: 'same-origin',
      headers: {
        'Accept': 'application/json'
      }
    })
      .then(response => {
        if (!response.ok) throw new Error('La respuesta no fue exitosa');
        return response.json();
      })
      .then(data => {
        if (data.session_expired) {
          console.warn("⏳ Sesión expirada. Redirigiendo...");
          window.location.href = '/account/logout/';
        } else {
          console.log("✅ Sesión activa");
        }
      })
      .catch(error => {
        console.error('❌ Error al verificar la sesión:', error);
      });
  }
// Detectar clics en cualquier parte de la página
document.addEventListener('click', function() {
    checkSession();  // Comprobar sesión en cada clic
});
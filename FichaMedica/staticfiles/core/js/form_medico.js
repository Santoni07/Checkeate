
    function toggleSearchMenu() {
        const searchContainer = document.getElementById('search-container');
        const antecedentesSection = document.getElementById('ficha_medica_section');
        searchContainer.style.display = 'none';
        antecedentesSection.style.display = 'block';
    }
    function toggleSection(sectionId) {
        const section = document.getElementById(sectionId);
        section.style.display = section.style.display === "none" ? "block" : "none";
    }

    function toggleForm(formId) {
        const form = document.getElementById(formId);
        form.style.display = form.style.display === "none" ? "block" : "none";
    }
   

    function toggleFields() {
        var estadoElement = document.getElementById("estado");

        if (!estadoElement) {
           
            return;
        }
    
        var estado = estadoElement.value;
        // Ahora podés usar `estado` sin problemas
        
        var fechaDeLlenadoDiv = document.getElementById("fecha_de_llenado_div");
        var fechaCaducidadDiv = document.getElementById("fecha_caducidad_div");
        var observacionDiv = document.getElementById("observacion_div");

          // Si el estado es "APROBADA", mostramos todos los campos
          if (estado === "APROBADA") {
            fechaDeLlenadoDiv.style.display = "block";
            fechaCaducidadDiv.style.display = "block";
            observacionDiv.style.display = "block";
        } 
        // Si el estado es "RECHAZADO", solo mostramos el campo de Observaciones
        else if (estado === "RECHAZADO") {
            fechaDeLlenadoDiv.style.display = "none";
            fechaCaducidadDiv.style.display = "none";
            observacionDiv.style.display = "block";
        } 
        // Si el estado es "PENDIENTE", todos los campos permanecen ocultos
        else {
            fechaDeLlenadoDiv.style.display = "none";
            fechaCaducidadDiv.style.display = "none";
            observacionDiv.style.display = "none";
        }
      
    }

    // Llamamos la función al cargar la página para ajustar la visibilidad de acuerdo con el estado inicial
    window.onload = toggleFields;
    document.addEventListener('DOMContentLoaded', function() {
        // Seleccionar todos los formularios con una clase común
        const forms = document.querySelectorAll('.ajax-form');
        
        forms.forEach(form => {
            // Crear un mensaje de éxito para cada formulario
            const successMessage = document.createElement('div');
            successMessage.classList.add('alert', 'alert-success', 'mt-3');
            successMessage.style.display = 'none';
            form.parentNode.appendChild(successMessage);
    
            // Agregar evento de envío a cada formulario
            form.addEventListener('submit', function(event) {
                event.preventDefault(); // Evitar el envío normal del formulario
                
                const formData = new FormData(form);
    
                fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        successMessage.textContent = data.message;
                        successMessage.style.display = 'block';
                        form.style.display = 'none'; // Ocultar formulario si es necesario
                    } else if (data.error) {
                        alert(data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
            });
        });
    });
    
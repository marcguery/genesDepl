function confSubmit(form) {
      if (confirm("Êtes-vous sûr ?")) {
      form.submit();
      }

      else {
      alert("Annulé !");
      }
      }
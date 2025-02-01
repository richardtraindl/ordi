
  function hinweis_speichern(){
    $("form").on("change", ":input", function(e){
      $(window).on('beforeunload', function(e){
        return "Es gibt ungespeicherte Änderungen.";
      });

      // Verhindern, dass ein Submit-Button (also z.B. "Speichern") auch den Hinweis hervorruft.
      $(this).parents("form:first").find(":submit").click(function(){ 
        $(window).off("beforeunload");
      });
    });
    
    $(".labor, .impfungen, .date").blur(function(e){
      if($(this).val().length > 0) {
        $(window).on('beforeunload', function(e){
          return "Es gibt ungespeicherte Änderungen.";
        });

        // Verhindern, dass ein Submit-Button (also z.B. "Speichern") auch den Hinweis hervorruft.
        $(this).parents("form:first").find(":submit").click(function() { $(window).off("beforeunload"); });
      }
    });

  }

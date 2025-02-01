
  function hinweis_speichern(){

    $('body').on('change keyup keydown', 'input, textarea, select', function(e){
      $(this).addClass('changed-input');
    });

    $('body').on('change blur', '.date', function(e){
      $(this).addClass('changed-input');
    });

    $(window).on('beforeunload', function(){
      if($('.changed-input').length){
        return 'You haven\'t saved your changes.';
      }
    });
        
    // Verhindern, dass ein Submit-Button (also z.B. "Speichern") auch den Hinweis hervorruft.
    $('input[type="submit"]').click(function(){ 
      $(window).off("beforeunload"); 
    });

  }
  
  
  

    




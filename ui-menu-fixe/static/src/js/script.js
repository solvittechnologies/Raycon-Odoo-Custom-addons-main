console.log('3333333333333333333')

document.addEventListener('click', function(e) {
    e = e || window.event;
    var target = e
        // text = target.textContent || target.innerText;

        // $(".dropdown-menu").removeClass("show");
    if (target.target.className==="btn btn-primary"){
        setTimeout(function() {
            $(".dropdown-menu").removeClass("show");
        }, 2000);

    }else if (target.target.nodeName==="SPAN"){

        setTimeout(function() {
            $(".dropdown-menu").removeClass("show");
        }, 2000);
    }
   

         
  }, false);


 


  $("body").click(function (e) { 
    
    $(".dropdown-menu").removeClass("show")
      
  });

/* This is just to show how one can use the "renders function", 
 * for a proper use of url hash, we would use something as Sammy.
 */
(function(){
  $("#wrapper").renders('page1');

  $("a[href=#page1]").live('click', function() {
    $("#wrapper").renders('page1', {
      user: "Luke"
    });
  });

  $("a[href=#page2]").live('click', function() {
    $("#wrapper").renders('page2', {
      user: "Vador"  
    });
  });
})();


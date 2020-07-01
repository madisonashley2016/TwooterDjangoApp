$(document).ready(function(){
    window.addEventListener("pageshow", function(e) {
    //Session storage is this awesome storage that doesnt go away till you close the browser.
    //This says if you got to this page through my back button, reload the page.
    if(sessionStorage.getItem("back_button_clicked")== "Yes"){
        sessionStorage.removeItem("back_button_clicked");
        window.location.reload();
    }
    });
    
    //Infinite back button.
    $(".header-back-button").on('click', function() {
        sessionStorage.setItem("back_button_clicked", "Yes");
        window.history.back();
    });
    
    //For my ability to paginate on scrolling.
    $.endlessPaginate({
        paginateOnScroll: true,
        paginateOnScrollMargin: 20,
        onCompleted: function(context, fragment) {
            $(".divgotourl").off('click').on('click', function(e){
                if(!$(e.target).is("button") && !$(e.target).is("i") && !$(e.target).is("a")){
                    window.location = $(this).attr("data-url");
                }
             });
            
            //When like button is clicked, send to server the clicked button. and its state.
            //off-click because need to turn off original event when paginate is called.
             $(".like-button").off('click').on('click', function(e) {
                e.preventDefault();
                var like = $(this).attr('data-id');
                var status = $(this).attr('data-status');
                buttonSocket.send(JSON.stringify( {
                    'like_id' : like,
                    'status' : status,
                    'type' : 'like'
                }));
            });
            $(".retwoot-button").off('click').on('click', function(e) {
                e.preventDefault();
                var twoot = $(this).attr('data-id');
                var status = $(this).attr('data-status');
        
                buttonSocket.send(JSON.stringify({
                    'retwoot_twoot_id' : twoot,
                    'status' : status,
                    'type' : 'retwoot'
                }));
                
            });
       
        }
    });

    //When you click this bit, it goes to url. Makes divs able to be urls.
    $(".divgotourl").click(function(e){
        if(!$(e.target).is("button") && !$(e.target).is("i") && !$(e.target).is("a")){
            window.location = $(this).attr("data-url");
        }
     });
    /*
    //This is just so that when you refresh the page it saves the location that you stopped at. 
    var scrollpos = localStorage.getItem('scrollpos'); //Get the last scroll pos.
    $(window).scrollTop(scrollpos); //Set the scroll pos
    $(window).on('unload', function(){ //Before window unloads, get the current scrollpos and save it.
        scrollpos = $(window).scrollTop();
        localStorage.setItem('scrollpos', scrollpos);
    });*/
    
    //************************************************************************

    //Web Socket stuff lit lit for the like button.
    //Create websocket buttonsocket, will be used for all main processes.
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    const buttonSocket = new WebSocket(
        ws_scheme + '://'
        + window.location.host
        + '/ws'
        + window.location.pathname
    );
    console.log("The websocket: " + buttonSocket);
    console.log("The url: " + window.location.host + '/ws' + window.location.pathname);

    //When like button is clicked, send to server the clicked button. and its state.
    $(".like-button").click(function(e) {
        e.preventDefault();
        var like = $(this).attr('data-id');
        var status = $(this).attr('data-status');
        buttonSocket.send(JSON.stringify( {
            'like_id' : like,
            'status' : status,
            'type' : 'like'
        }));
    });
    $(".retwoot-button").click(function(e) {
        e.preventDefault();
        var twoot = $(this).attr('data-id');
        var status = $(this).attr('data-status');

        buttonSocket.send(JSON.stringify({
            'retwoot_twoot_id' : twoot,
            'status' : status,
            'type' : 'retwoot'
        }));
        
    });
     //Submit the new twoot data to view. On success, send to websocket to broadcast to all online users.
     var tcform = $("#twoot-create-form-id");   
     tcform.submit(function(e) {
         var tcformdata = tcform.get(0);
         
         e.preventDefault();
         $.ajax({
             type: tcform.attr('method'),
             url: tcform.attr('action'),
             data: new FormData(tcformdata),
             processData: false,
             contentType: false,
             success: function(data){
                 console.log("Success on returning ajax method -- Twoot style!!.");
                 console.log("Here is our data");
                 console.log("twoot_html: " + data.twoot_html);
                 console.log("twoot_html1: " + data.twoot_html1);
                 console.log("twoot_html2: " + data.twoot_html2);
                 console.log("Now we send over our sexy data...");
                 buttonSocket.send(JSON.stringify( {
                     'twoot_html' : data.twoot_html,
                     'twoot_html1' : data.twoot_html1,
                     'twoot_html2' : data.twoot_html2,
                     'type' : 'create_twoot'
                 }));
             },
             error: function(data){
                 console.log("FAILURE FAILURE FAILURE REEEEEE!!!");
             }
         });
         return false;
     });
     var ccform = $("#comment-create-form-id");   
     ccform.submit(function(e) {
         var ccformdata = ccform.get(0);
         e.preventDefault();
         $.ajax({
             type: ccform.attr('method'),
             url: ccform.attr('action'),
             data: new FormData(ccformdata),
             processData: false,
             contentType: false,
             success: function(data){
                 console.log("Success on returning ajax method -- comment style!.");
                 console.log("Here is our data");
                 console.log("twoot_html: " + data.twoot_html);
                 console.log("twoot_html1: " + data.twoot_html1);
                 console.log("twoot_html2: " + data.twoot_html2);
                 console.log("parent_pk: " + data.parent_pk);
                 console.log("Now we send over our sexy data...");
                 buttonSocket.send(JSON.stringify( {
                     'twoot_html' : data.twoot_html,
                     'twoot_html1' : data.twoot_html1,
                     'twoot_html2' : data.twoot_html2,
                     'parent_pk' : data.parent_pk,
                     'type' : 'create_comment'
                 }));
             },
             error: function(data){
                 console.log("FAILURE FAILURE FAILURE REEEEEE!!!");
             }
         });
         return false;
     });
    //Recieve data back from socket, post to frontend as needed.
    buttonSocket.onmessage = function(e) {
        var data = JSON.parse(e.data);
        if(data.type == 'like'){
            $(".like-button[data-id='"+ data.like_id + "']").each(function() {
                var num_likes = parseInt($(this).next().text());
                var i_am_liker = data.i_am_liker;

                if(data.status == "liked"){
                    num_likes += 1;
                   $(this).next().text(num_likes);
                    if (i_am_liker == true){
                        $(this).attr('data-status','liked');
                        $(this).html(`<i class='bx bxs-heart'></i>`);
                        $(this).attr('class', 'like-button red twoot-button');
                        $(this).next().addClass('red-no-hover');
                    }
                }
                else if(data.status == "not_liked"){
                    num_likes -= 1;
                    $(this).next().text(num_likes);
                    if (i_am_liker == true){
                        $(this).attr('data-status','not_liked');
                        $(this).html(`<i class='bx bx-heart'></i>`);
                        $(this).attr('class', 'like-button red-unclicked twoot-button');
                        $(this).next().removeClass('red-no-hover');
                    }
                }

            });
            
        }
        if(data.type == 'create_twoot'){
            //if username in data.usernames of following, then prepend to main view. else just to explore.
            //Also for everyone, prepend to profile page.
           var profile_list = "#profile_view-twoot-list-id-" + data.sender_username;
           var profile_replies_list = "#replies_view-twoot-list-id-" + data.sender_username;
           $(profile_list).prepend(data.twoot_html); //Append to senders profile
           $(profile_replies_list).prepend(data.twoot_html); //Append to senders replies profile
            $("#explore-twoot-list-id-explore_view_latest").prepend(data.twoot_html); //append to explore latest
            if(data.in_followers){
                $("#twoots-twoot-list-id-main_view_latest").prepend(data.twoot_html);
            }
            if(data.me){ //If im the one who sent the twoot.
                $(".twoot-create-input").val(null); //Reset form values.
                $("#twoot-create-file-id").replaceWith($("#twoot-create-file-id").val('').clone(true));
                $('#twoot-create-img-id').attr('src', '');
                $(".create-twoot-img-container-delete").css('display', 'none');
                $('#twoot-create-img-id').css('display', 'none');
                $("#main-twoot-submit-button-id").prop("disabled", true);
                $("#twoot-create-label").attr('class', 'twoot-create-header-disabled button');
                $("#side1-button-id").css("display", "none");
                $("#side2-button-id").css("display", "none");
                $("#side3-button-id").css("display", "none");
                $(".letters-typed").html("<i class='bx bx-no-entry'></i>");

                $("#twoots-twoot-list-id-main_view").prepend(data.twoot_html);
                $("#twoots-twoot-list-id-main_view_latest").prepend(data.twoot_html);
                if(window.location.pathname == '/twoot/'){ //If using the twoot button page, you want it to refresh. 
                    window.location = document.referrer;   
                }
            }
        }  
        if(data.type == 'create_comment'){ //Also prepend to replies page.
            var profile_replies_list = "#replies_view-twoot-list-id-" + data.sender_username;
            $(profile_replies_list).prepend(data.twoot_html); //Append to senders profile replies
            $("#comments-twoot-list-id-" + data.parent_pk).prepend(data.twoot_html); //append to comments.
            if(data.me){
                window.location = document.referrer;
            }
        } 
        if(data.type == 'retwoot'){ //Add appending to top of ur profile as well...
            
            //Add to retwoot count for all instances of this post that are loaded.
            $(".retwoot-button[data-id=" + data.twoot_id + "]").each(function() {
                var retwoot_count = parseInt($(this).next().text());
                console.log("retwoot count: " + retwoot_count);
                retwoot_count += 1;
                $(this).next().html(retwoot_count);
            });
            if(data.me){//If I am the retwooter, append to my main view as well, and make the button green on both posts.
                $(".retwoot-button[data-id=" + data.twoot_id + "]").each(function() { //make original post button green.
                    $(this).removeClass("green-unclicked");
                    $(this).addClass("green");
                    $(this).next().addClass("green-no-hover");
                    $(this).attr("data-status", "retwooted");
                });
                $("#twoots-twoot-list-id-main_view").prepend(data.twoot_html);//Add new retwoot post, should be green by default.
            }
            //Append to all of ur followers latest page.
            $("#twoots-twoot-list-id-main_view_latest").prepend(data.twoot_html); //Should be green if they have retwooted it.
            
        }
        if(data.type == 'retwoot_delete'){
            console.log("Delete!");
            $(".retwoot-button[data-id=" + data.twoot_id + "]").each(function() { //Deencrement the count.
                var retwoot_count = parseInt($(this).next().text());
                retwoot_count = retwoot_count - 1;
                $(this).next().html(retwoot_count);
            })
            //If delete, then get all retwoots that have got id=one that was deleted, and remove them.
            var pk = "retwoot_" + data.delete_id;
            $(".twoot[data-twoot-id=" + pk + "]").each( function() {
                console.log("each! delete_id: " + data.delete_id +" my data_twoot_id: " + $(this).attr("data-twoot-id"));
                $(this).css("display", "none");
            });
            if(data.me){ //on original post, if I am the retwooter, then fix the retwoot button back to grey and shit.
                $(".retwoot-button[data-id=" + data.twoot_id + "]").each(function() {
                    $(this).removeClass("green");
                    $(this).addClass("green-unclicked");
                    $(this).next().removeClass("green-no-hover");
                    $(this).attr("data-status", "not_retwooted");
                });
            }
        }
        if(data.type == 'create_twoot' || data.type == 'create_comment' || data.type == 'retwoot' || data.type == 'retwoot_delete'){
            $(".like-button").off('click').on('click', function(e) { //Reset like button after submitting new tweet.
                e.preventDefault();
                var like = $(this).attr('data-id');
                var status = $(this).attr('data-status');
                buttonSocket.send(JSON.stringify( {
                    'like_id' : like,
                    'status' : status,
                    'type' : 'like'
                }));
            });
            $(".retwoot-button").off('click').on('click', function(e) {
                e.preventDefault();
                var twoot = $(this).attr('data-id');
                var status = $(this).attr('data-status');
        
                buttonSocket.send(JSON.stringify({
                    'retwoot_twoot_id' : twoot,
                    'status' : status,
                    'type' : 'retwoot'
                }));
                
            });
            $(".divgotourl").off('click').on('click', function(e){
                if(!$(e.target).is("button") && !$(e.target).is("i") && !$(e.target).is("a")){
                    window.location = $(this).attr("data-url");
                }
            });
        }
       
    };
    //If channel closes...
    buttonSocket.onclose = function(e) { 
        console.error("Button socket closed unexpectedly!!");
    }; 

});







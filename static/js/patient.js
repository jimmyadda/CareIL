$(document).ready(function () {

    var table
    
    function addPatient(data) {

        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "patientapi",
            "method": "POST",
            "headers": {
                "content-type": "application/json",
                "cache-control": "no-cache",
                "postman-token": "2612534b-9ccd-ab7e-1f73-659029967199"
            },
            "processData": false,
            "data": JSON.stringify(data)
        }

        $.ajax(settings).done(function (response) {
            $('.modal.in').modal('hide');
            var lang = document.getElementById('lang').value
            let notif = "Client Added Successfully"
            if(lang=="HE"){notif= "מטופל התווסף בהצלחה"}
            $.notify(notif, {"status":"success"});

            table.destroy();
            $('#datatable4 tbody').empty(); // empty in case the columns change
            //send wellcome mail
            console.log(data)
            let f = new FormData();
            f.append("pat_email",data.pat_email)
            f.append("lang",data.lang)
            fetch("/SendNotification",{
            "method": "POST",
            "body":f,       
            }).then(response => response.text()).then(data => {               
            });
            getPatient()
        });

    }

    function deletePatient(id) {
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "patientapi/" + id,
            "method": "DELETE",
            "headers": {
                "cache-control": "no-cache",
                "postman-token": "28ea8360-5af0-1d11-e595-485a109760f2"
            }
        }

swal({
    title: "Are you sure?",
    text: "You will not be able to recover this data",
    type: "warning",
    showCancelButton: true,
    confirmButtonColor: "#DD6B55",
    confirmButtonText: "Yes, delete it!",
    closeOnConfirm: false
}, function() {
 $.ajax(settings).done(function (response) {
   swal("Deleted!", "Client has been deleted.", "success");
            table.destroy();
            $('#datatable4 tbody').empty(); // empty in case the columns change
            getPatient()
        });


});

    }

    function updatePatient(data, id) {
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "patientapi/" + id,
            "method": "PUT",
            "headers": {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            "processData": false,
            "data": JSON.stringify(data)
        }

        $.ajax(settings).done(function (response) {
            $('.modal.in').modal('hide')
            $.notify("Client Updated Successfully", {"status":"success"});
            table.destroy();
            $('#datatable4 tbody').empty(); // empty in case the columns change
            getPatient()
        });


    }

    function getPatient() {

        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "patientapi",
            "method": "GET",
            "headers": {
                "cache-control": "no-cache"
            }
        }

        $.ajax(settings).done(function (response) {
            table = $('#datatable4').DataTable({
                "bDestroy": true,
                'paging': true, // Table pagination
                'ordering': true, // Column ordering
                'info': true, // Bottom left status text
                aaData: response,
                 "aaSorting": [],
                aoColumns: [
                    {
                        mData: 'pat_first_name'
                    },
                    {
                        mData: 'pat_last_name'
                    },
                    {
                        mData: 'pat_insurance_no'
                    },
                    {
                        mData: 'pat_dob'
                    },
                    {
                        mData: 'pat_address'
                    },
                    {
                        mData: 'pat_email'
                    },
                    {
                        mData: 'pat_ph_no'
                    },
                    {
                        mRender: function (o) {
                            return '<button key="editbtn" id="patedit"  class="btn-xs btn btn-info btn-edit edit-btn translate EN" type="button">Edit</button>';
                        }
                    },
                    {
                        mRender: function (o) {
                            
                            return '<button key="patrecbtn" id="patrecords" class="folder-btn btn-xs btn btn-success translate EN" type="button">Client Profile</button>';
                        }
                    },
                    {
                        mRender: function (o) {
                            return '<button  key="deletebtn" class="btn-xs btn btn-danger delete-btn translate EN" type="button">Delete</button>';
                        }
                    }
        ]
            });
            $('#datatable4 tbody').on('click', '.delete-btn', function () {
                var data = table.row($(this).parents('tr')).data();
                console.log(data)
                deletePatient(data.pat_id)
            });


            //Edit patient modal            
            $('#datatable4 tbody').on('click', '.edit-btn',function () {
                var data = table.row($(this).parents('tr')).data();
                $('#myModal').modal().one('shown.bs.modal', function (e) {
                    //display data
                    for (var key in data) {
                        $("[name=" + key + "]").val(data[key])
                    }
                    ///
                    $("#savethepatient").off("click").on("click", function(e) {
                    var instance = $('#detailform').parsley();
                    instance.validate()
                            if(instance.isValid()){
                        jsondata = $('#detailform').serializeJSON();
                        updatePatient(jsondata, data.pat_id)
                        }
        
                    })
        
                })                    
            })


            $('#datatable4 tbody').on('click', '.folder-btn',function () {
                var data = table.row($(this).parents('tr')).data();
                let json_data = JSON.stringify(data)
                console.log(json_data);
                sessionStorage.setItem("pat_det", json_data);
                window.open("/patientform?id="+data.pat_id);
            })
       //call 
       //language
       console.log(my_lang,Translate_jsonData)
       if(my_lang=="HE"){
       translate_DOM_element('translate',Translate_jsonData,'EN',my_lang);     
       }
       else{
       translate_DOM_element('translate',Translate_jsonData,'HE',my_lang);  
       }   
          
        });


    }

    $("#addpatient").click(function () {
        $('#detailform input,textarea').val("");
        var selected_my_lang = sessionStorage.getItem("lang");
        if(!selected_my_lang){selected_my_lang="EN"}
        document.getElementById('lang').value = selected_my_lang;
        

        $('#myModal').modal().one('shown.bs.modal', function (e) {
            $("#savethepatient").off("click").on("click", function(e) {
            var instance = $('#detailform').parsley();
            instance.validate()
                    if(instance.isValid()){
                jsondata = $('#detailform').serializeJSON();
                addPatient(jsondata)
                }

            })

        })



    })


getPatient()


function getPatientById(pat_id) {

    var settings = {
        "async": true,
        "crossDomain": true,
        "url": "patientapi?id=" + pat_id,
        "method": "GET",
        "headers": {
            "cache-control": "no-cache"
        }
    }

    $.ajax(settings).done(function (response) {

        table = $('#datatable4').DataTable({
            "bDestroy": true,
            'paging': true, // Table pagination
            'ordering': true, // Column ordering
            'info': true, // Bottom left status text
            aaData: response,
             "aaSorting": [],
            aoColumns: [
                {
                    mData: 'pat_first_name'
                },
                {
                    mData: 'pat_last_name'
                },
                {
                    mData: 'pat_insurance_no'
                },
                {
                    mData: 'pat_dob'
                },
                {
                    mData: 'pat_address'
                },
                {
                    mData: 'pat_email'
                },
                {
                    mData: 'pat_ph_no'
                },
                {
                    mRender: function (o) {
                        return '<button key="editbtn" id="patedit" class="btn-xs btn btn-info btn-edit translate EN" type="button">Edit</button>';
                    }
                },
                {
                    mRender: function (o) {
                        
                        return '<button id="patrecords" class="btn-xs btn btn-success edit-btn translate EN" type="button">Client Profile</button>';
                    }
                },
                {
                    mRender: function (o) {
                        return '<button  key="deletebtn" class="btn-xs btn btn-danger delete-btn translate EN" type="button">Delete</button>';
                    }
                }
    ]
        });
        $('#datatable4 tbody').on('click', '.delete-btn', function () {
            var data = table.row($(this).parents('tr')).data();
            console.log(data)
            deletePatient(data.pat_id)
        });


        //Edit patient modal
        $("#patedit").click(function () {
            var data = table.row($(this).parents('tr')).data();
            $('#myModal').modal().one('shown.bs.modal', function (e) {
                //display data
                for (var key in data) {
                    $("[name=" + key + "]").val(data[key])
                }
                ///
                $("#savethepatient").off("click").on("click", function(e) {
                var instance = $('#detailform').parsley();
                instance.validate()
                        if(instance.isValid()){
                    jsondata = $('#detailform').serializeJSON();
                    updatePatient(jsondata, data.pat_id)
                    }
    
                })
    
            })                    
        })
      

    });


}

$("#emailinput").bind('blur', function(event)  {
    var testVal = document.getElementById("emailinput").value 
    if (testVal != "") {
        ValidateEmail(document.getElementById("emailinput"));
    }
});

$("#zehutinput").bind('blur', function(event)  {
    var testVal = document.getElementById("zehutinput").value 
    if (testVal != "") {
        ValidatePatientIDno(document.getElementById("zehutinput"));
    }
});




})


   function ValidateEmail(inputText)
   {
           var mailformat = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?$/;
           if(inputText.value.match(mailformat))
           {
            $('#invalid_email').text("Entered Email is Valid!!");
            $('#invalid_email').css("color", "green");
           return true;
           }
           else
           {
            $('#invalid_email').text("Entered Email is not Valid!!");
            $('#invalid_email').css("color", "red");
           return false;
           }
   }

   function ValidatePatientIDno(inputText)
   {
           var mailformat = /\d{9}/;
           if(inputText.value.match(mailformat))
           {
            $('#invalid_zehutinput').text("OK!");
            $('#invalid_zehutinput').css("color", "green");
           return true;
           }
           else
           {
            $('#invalid_zehutinput').text("מספר ת.ז לא תקין");
            $('#invalid_zehutinput').css("color", "red");
           return false;
           }
   }

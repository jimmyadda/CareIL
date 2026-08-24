$(document).ready(function () {

    var table


    function addDoctor(data) {
        console.log(data);
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "/doctorapi",
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
            $('.modal.in').modal('hide')
            //Get LAng
            var my_lang = sessionStorage.getItem("lang");
            if(my_lang=="HE"){
            $.notify("מטפל התווסף בהצלחה", {"status":"success"}); 
            }
            else{
                $.notify("Therapist Added Successfully", {"status":"success"});
            } 
            table.destroy();
            $('#datatable4 tbody').empty(); // empty in case the columns change
            getDoctor()
        });

    }

    function deleteDoctor(id) {
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "/doctorapi/" + id,
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
        }, function () {
            $.ajax(settings).done(function (response) {
                swal("Deleted!", "Therapist has been deleted.", "success");
                table.destroy();
                $('#datatable4 tbody').empty(); // empty in case the columns change
                getDoctor()
            });


        });

    }

    function updateDoctor(data, id) {
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "/doctorapi/" + id,
            "method": "PUT",
            "headers": {
                "content-type": "application/json",
                "cache-control": "no-cache"
            },
            "processData": false,
            "data": JSON.stringify(data)
        }

        $.ajax(settings).done(function (response) {
                        //Get LAng
                        var my_lang = sessionStorage.getItem("lang");
                        if(my_lang=="HE"){
                        $.notify("מטפל התווסף בהצלחה", {"status":"success"}); 
                        }
                        else{
                            $.notify("Therapist Added Successfully", {"status":"success"});
                        } 
            $('.modal.in').modal('hide')
            table.destroy();
            $('#datatable4 tbody').empty(); // empty in case the columns change
            getDoctor()
        });


    }

    function getDoctor() {

        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "/doctorapi",
            "method": "GET",
            "headers": {
                "cache-control": "no-cache"
            }
        }

        $.ajax(settings).done(function (response) {
            console.log(response);
            $('#create-therapist-row').toggle(response.length === 0);
            table = $('#datatable4').DataTable({
                "bDestroy": true,
                'paging': true, // Table pagination
                'ordering': true, // Column ordering
                'info': true, // Bottom left status text
                aaData: response,
                  "aaSorting": [],
                aoColumns: [
                    {
                        mData: 'doc_first_name'
                    },
                    {
                        mData: 'doc_last_name'
                    },
                    {
                        mData: 'doc_address'
                    },
                    {
                        mData: 'doc_ph_no'
                    },
                    {
                        mData: 'doc_email'
                    },
                    {
                        mRender: function (o) {
                            return '<button key="editbtn" class="btn-xs btn btn-info btn-edit translate EN" type="button">Edit</button>';
                        }
                    }
        ]
            });
            $('.btn-edit').one("click", function (e) {
                var data = table.row($(this).parents('tr')).data();
                $('#myModal').modal().one('shown.bs.modal', function (e) {
                    for (var key in data) {
                        $("[name=" + key + "]").val(data[key])
                    }
                    $("#savethepatient").off("click").on("click", function (e) {
                        var instance = $('#detailform').parsley();
                        instance.validate()
                        console.log(instance.isValid())
                        if (instance.isValid()) {
                            jsondata = $('#detailform').serializeJSON();
                            updateDoctor(jsondata, data.doc_id)
                        }

                    })
                })



            });

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
        const jsondata2 = $('#detailform').serializeJSON();
        console.log(jsondata2);

        //$('#detailform input,textarea').val("")
        $('#myModal').modal().one('shown.bs.modal', function (e) {
            $("#savethepatient").off("click").on("click", function (e) {
                var instance = $('#detailform').parsley();
                instance.validate()
                if (instance.isValid()) {
                    jsondata = $('#detailform').serializeJSON();
                    console.log(jsondata);
                    addDoctor(jsondata)
                }

            })

        })



    })


    getDoctor()
})

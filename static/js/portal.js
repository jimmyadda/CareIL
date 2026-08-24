$(document).ready(function () {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const patienid = urlParams.get('patid')

//Modal Form 

function test(patienid){

  $('#myModal').show('show', function() {
  
    $("#patient_select").val(patienid);

         //disable datetime
         var disabletime = $('#unavailableHours').val().split(',');
         disabletime = changearrformat(disabletime);


    availabilityPickerOptions(disabletime).then(function (options) {
      $(".form_datetime").datetimepicker(options);
      attachBookedSlotGuard($(".form_datetime"), disabletime);
    });


  $("#closemodal").off("click").on("click", function(e) {
    $('#myModal').hide();
    });

  $("#savethepatient").off("click").on("click", function(e) {
    var instance = $('#detailform').parsley();
    instance.validate()
     if(instance.isValid()){
        jsondata = $('#detailform').serializeJSON();
        let pat_id = jsondata.pat_id;
        var res = "";
        var available =  checkdate(jsondata).
        then(response => 
          {
            if(response=="OK")
            {
              addAppointment(jsondata);
            }
            else{
              swal("Oops...", "This date is unavailable!", "error");
            }
          }); 
      
        }
      
    });
});

}

async function checkdate(data){
  //Check Date 
  let f = new FormData();
  f.append("appointmentdate",data.appointment_date)
  f.append("pat_id",data.pat_id)
  console.log('checkdate')
  const response = await fetch("/checkdate",{
  "method": "POST",
  "body":f,       
  })
  const chedatdate = await response.text();
  return chedatdate;
}

 function addAppointment(data) {
  var table;

  var settings = {
      "async": true,
      "crossDomain": true,
      "url": "appointmentrequestapi",
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
   $('#myModal').hide();
   swal("Appointment request was submitted Successfully!", "");   
  });
   
}


async function getDoctor() {
  var doctorSelect="";
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "doctorapi",
            "method": "GET",
            "headers": {
                "cache-control": "no-cache"
            }
        }

        $.ajax(settings).done(function (response) {
        for(i=0;i<response.length;i++){

        response[i].doc_fullname=response[i].doc_first_name+" "+response[i].doc_last_name
        
        doctorSelect +="<option value="+response[i].doc_id+">"+response[i].doc_fullname+"</option>"
        }

        $("#doctor_select").html(doctorSelect);
        })

      
        }


async function getPatient(patienid) {
      var patientSelect="";
        var settings = {
            "async": true,
            "crossDomain": true,
            "url": "patientapi?id="+ patienid,
            "method": "GET",
            "headers": {
                "cache-control": "no-cache"
            }
        }

        $.ajax(settings).done(function (response) {
         for(i=0;i<response.length;i++){
          response[i].pat_fullname=response[i].pat_first_name+" "+response[i].pat_last_name
          if(response[i].pat_id == patienid){
            patientSelect +="<option selected value="+response[i].pat_id+">"+response[i].pat_fullname+"</option>"
          }
        }          
        $("#patient_select").html(patientSelect)
                })
                
        }


        $("#addpatient").click(async function () {
          const queryString = window.location.search;
          const urlParams = new URLSearchParams(queryString);
          const patienid = urlParams.get('pat_id')

         await getDoctor();

         await getPatient(patienid);

          test(patienid);
        })



})

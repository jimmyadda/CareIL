
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const Lang = urlParams.get('lang')

    function translate_DOM_element(cssclass,jsonobj,fromlanguage,tolanguage){
        tolanguage = tolanguage || "EN";
        const translate_Json= jsonobj
        const from_lang = fromlanguage;
        const to_lang = tolanguage; 
        console.log(translate_Json)

        $('.'+cssclass).each(function(i, obj) {
            //search in JSON by key & lang
            var obj_text = $(obj).text()
            var obj_key = $(obj).attr('key');     
            var objType = $(obj).get(0).tagName; //if INPUT change val() not text()


            var translated_text  = translate_Json[tolanguage][obj_key]
            if(translated_text){
            $(obj).text(translated_text);
            if(objType=="INPUT"){$(obj).val(translated_text);}
            }
            

            //Load css for to lang        
            $(obj).removeClass(fromlanguage);
            $(obj).addClass(tolanguage);
            
        });

        // Translate form hints as well as visible element text. Existing keys
        // remain the source of truth, so language selection behavior is unchanged.
        const placeholderKeys = {
            'first name': 'firstname',
            'last name': 'lastname',
            'id no': 'IDNum',
            'id number': 'IDNum',
            'insurance no': 'insuranceNo',
            'date of birth': 'dob',
            'phone number': 'phone',
            'email': 'email',
            'email address': 'email',
            'address': 'address',
            'please select patient': 'selectClient',
            'please select client': 'selectClient',
            'please select doctor': 'selectTherapist',
            'please select therapist': 'selectTherapist',
            'new type name': 'newTypeName',
            'enter your email': 'enterEmail',
            'enter you email': 'enterEmail',
            'write something..': 'writeSomething',
            'userid': 'username',
            'password': 'password',
            'name': 'name',
            'enter the verification code': 'verificationCode',
            'leave blank to keep the current password': 'keepPassword',
            'type and hit enter ...': 'searchPlaceholder'
        };
        $('[placeholder]').each(function () {
            const element = $(this);
            const original = element.attr('data-i18n-placeholder') || element.attr('placeholder') || '';
            if (!element.attr('data-i18n-placeholder')) element.attr('data-i18n-placeholder', original);
            const key = element.attr('data-placeholder-key') || element.attr('key') || placeholderKeys[original.trim().toLowerCase()];
            const translated = key && translate_Json[tolanguage] && translate_Json[tolanguage][key];
            if (translated) element.attr('placeholder', translated);
        });
    
        if(tolanguage == "HE"){
        $("body").removeClass("clinic-lang-en").addClass("clinic-lang-he");
        $("body").css("direction","rtl");
        $("body").css("text-align","right");
        $('#pullcss').removeClass('pull-right').addClass('pull-left');    
        $('#pullcss1').removeClass('pull-right').addClass('pull-left');     
        }
        else{
            $("body").removeClass("clinic-lang-he").addClass("clinic-lang-en");
            $("body").css("direction","ltr");
            $("body").css("text-align","left");
            $('#pullcss').removeClass('pull-left').addClass('pull-right');
            $('#pullcss1').removeClass('pull-left').addClass('pull-right');

            }
    }




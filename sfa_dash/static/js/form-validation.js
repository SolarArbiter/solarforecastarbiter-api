MAX_FILESIZE = 16 * 1024 * 1024;
$(document).ready(function(){
    // Custom validity handlers to supply users with more meaningful messages
    // when they provide invalid input.
    if(document.getElementsByName('name').length >0){
        // Listen for invalid input
        document.getElementsByName('name')[0].addEventListener(
            'invalid', function(){
                this.setCustomValidity(
                    `Name may only contain characters a-zA-Z0-9(), -'_.`);
            }
        );
        // clear any invalid state and check for validity to trigger an invalid
        // event
        document.getElementsByName('name')[0].addEventListener(
            'input',function(){
                this.setCustomValidity('');
                this.checkValidity();
            }
        );
    }

    // Validate file uploads are within the required range
    $('input:file').change(function(){
        if(this.files.length > 0){
            if(this.files[0].size > MAX_FILESIZE){
                $(this).after(
                    $('<div>')
                        .addClass(['alert', 'alert-danger'])
                        .html(
                            `The file selected is too large. The maximum file
                             upload file size is
                             ${MAX_FILESIZE / (1024 * 1024)}MB. Your file is
                             ${(this.files[0].size / (1024 * 1024)).toFixed(4)}
                             MB.`)
                );
                $('button:submit').prop('disabled', true);
            } else {
                $('button:submit').prop('disabled', false);
            }
        }
    });
    // Ensure interval_label of 'Event'  when event variable is selected.
    $('[name="variable"]').change(function(){
        var interval_label_input = $('[name="interval_label"]');
        if (interval_label_input.val() != 'event'){
            // Store a previous non-event value
            previous_interval_label = interval_label_input.val();
        }
        interval_label_input.find('option').prop('hidden', false);

        if(this.value == 'event'){
            interval_label_input.val('event');
            interval_label_input.find('option').not('[value="event"]').prop(
                'hidden', true);
        } else {
            if(interval_label_input.val() == 'event'){
                // if variable was changed from event, and interval label is
                // still set, restore the previous non-event interval label
                interval_label_input.val(previous_interval_label);
            }
            interval_label_input.find('option[value="event"]').prop(
                'hidden', true);
        }
    });
    // hide interval_label = 'event' by default.
    $('[name="interval_label"] option[value="event"]').prop('hidden', true);

    $('[name="permission-action"]').change(function(){
        if (this.value == 'create'){
            $('#non-create-permission-fields')
                .prop('disabled', true)
                .collapse('hide');
            $('#create-permission-explanation')
                .prop('hidden', false)
                .collapse('show');
        } else {
            $('#non-create-permission-fields')
                .prop('disabled', false)
                .collapse('show');
            $('#create-permission-explanation')
                .prop('hidden', true)
                .collapse('hide');
        }
    });
});

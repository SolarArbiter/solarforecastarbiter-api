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
});

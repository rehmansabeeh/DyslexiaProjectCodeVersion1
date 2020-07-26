$(document).ready(function() {

	$('form').on('submit', function(event) {

		$.ajax({
			data : {
				name : $('#edit').val()
			},
			type : 'POST',
			url : '/'
		})
		.done(function(data) {
		});

		event.preventDefault();

	});

});
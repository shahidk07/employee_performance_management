// Main UI Script for EPMS

$(document).ready(function() {
    // 1. Mobile Sidebar Toggle
    $('#mobile-menu-button').on('click', function() {
        $('#sidebar').toggleClass('-translate-x-full');
    });

    $('#close-sidebar-button').on('click', function() {
        $('#sidebar').addClass('-translate-x-full');
    });

    // 2. Initialize DataTables automatically on tables with class 'datatable'
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            responsive: true,
            pageLength: 10,
            lengthMenu: [5, 10, 25, 50],
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search records...",
                lengthMenu: "Show _MENU_ entries",
                paginate: {
                    first: '<i class="fa-solid fa-angles-left"></i>',
                    last: '<i class="fa-solid fa-angles-right"></i>',
                    previous: '<i class="fa-solid fa-angle-left"></i>',
                    next: '<i class="fa-solid fa-angle-right"></i>'
                }
            },
            drawCallback: function() {
                // Apply Tailwind classes to pagination buttons
                $('.dataTables_paginate').addClass('flex items-center gap-1 mt-4');
                $('.paginate_button').addClass('px-3 py-1 text-sm border border-slate-200 rounded-md hover:bg-slate-100 transition-colors cursor-pointer');
                $('.paginate_button.current').addClass('bg-blue-600 text-white border-blue-600 hover:bg-blue-700 hover:text-white');
                $('.paginate_button.disabled').addClass('opacity-50 pointer-events-none');
            }
        });
    }

    // 3. SweetAlert2 Confirmation for deletes and status changes
    $(document).on('click', '.confirm-delete', function(e) {
        e.preventDefault();
        const form = $(this).closest('form');
        const entityName = $(this).data('entity') || 'record';
        
        Swal.fire({
            title: `Delete ${entityName}?`,
            text: "This action cannot be undone!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit();
            }
        });
    });

    $(document).on('click', '.confirm-action', function(e) {
        e.preventDefault();
        const href = $(this).attr('href');
        const actionText = $(this).data('action') || 'perform this action';
        
        Swal.fire({
            title: 'Are you sure?',
            text: `Do you want to ${actionText}?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3b82f6',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Yes, proceed!',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = href;
            }
        });
    });

    // 4. Highlight active sidebar link
    const currentPath = window.location.pathname;
    $('#sidebar nav a').each(function() {
        const linkPath = $(this).attr('href');
        if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
            $(this).addClass('sidebar-link-active');
        }
    });
});

// Toast function for notifications
function showToast(icon, message) {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3500,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    });

    Toast.fire({
        icon: icon,
        title: message
    });
}

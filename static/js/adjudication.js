// Add this at the very top of your script
document.addEventListener('DOMContentLoaded', function() {
    console.log("Adjudication script loaded successfully");
    
    // Initialize form submission handler with fixed code
    if (document.getElementById('adjudicationForm')) {
        document.getElementById('adjudicationForm').addEventListener('submit', handleFormSubmission);
    }
    
    // Function to check adjudication status
    function checkAdjudicationStatus(ticketId) {
        return new Promise((resolve) => {
            // First check if the violation card still exists
            const violationCard = document.querySelector(`.violation-card[data-violation-id="${ticketId}"]`);
            if (!violationCard) {
                console.log(`Violation card for ticket ${ticketId} no longer exists - likely adjudicated`);
                return resolve(true);
            }
            
            // Server-side verification
            fetch(`/adjudication/violation/${ticketId}/check-status/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.is_adjudicated) {
                    console.log(`Server confirmed ticket ${ticketId} was adjudicated`);
                    resolve(true);
                } else {
                    resolve(false);
                }
            })
            .catch(error => {
                console.error('Error checking status:', error);
                resolve(false); // Conservative approach
            });
        });
    }
    
    // Main form submission handler - completely rewritten
    function handleFormSubmission(event) {
        event.preventDefault();
        
        // Get form data
        const ticketId = document.getElementById('ticketId').value;
        const penaltyAmount = document.getElementById('penaltyAmount').value;
        const notes = document.getElementById('adjudicationNotes').value;
        
        // Validate
        if (!ticketId || !penaltyAmount) {
            Swal.fire({
                icon: 'error',
                title: 'Missing Data',
                text: 'Please ensure you have selected a violation and entered a penalty amount.',
                confirmButtonColor: 'var(--primary-color)'
            });
            return;
        }
        
        // Get violation types
        const selectedTypes = [];
        document.querySelectorAll('.violation-type-checkbox:checked').forEach(checkbox => {
            selectedTypes.push(checkbox.value);
        });
        
        // Get removed violations
        const removedViolations = {};
        document.querySelectorAll('.violation-type-checkbox:not(:checked)').forEach(checkbox => {
            const violationType = checkbox.value;
            const reason = checkbox.getAttribute('data-removal-reason') || 'No reason provided';
            const amount = checkbox.getAttribute('data-amount') || '0.00';
            
            removedViolations[violationType] = {
                reason: reason,
                amount: amount
            };
        });
        
        // Get interest data
        const interestAmount = document.getElementById('interestAmount') ? 
            parseFloat(document.getElementById('interestAmount').textContent || '0') : 0;
        const totalWithInterest = document.getElementById('totalWithInterest') ? 
            parseFloat(document.getElementById('totalWithInterest').textContent || penaltyAmount) : parseFloat(penaltyAmount);
        const includesInterest = document.getElementById('includeInterest') ? 
            document.getElementById('includeInterest').checked : false;
        
        // Confirmation dialog
        Swal.fire({
            title: 'Confirm Adjudication',
            text: 'Are you sure you want to submit this adjudication decision?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: 'var(--primary-color)',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Yes, Submit',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                // Show loading state
                Swal.fire({
                    title: 'Processing...',
                    html: '<div class="spinner-border text-primary" role="status"></div>',
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
                
                // Create request data
                const requestData = {
                    ticket_id: ticketId,
                    violation_types: selectedTypes,
                    penalty_amount: penaltyAmount,
                    notes: notes,
                    interest_amount: interestAmount,
                    total_with_interest: totalWithInterest,
                    includes_interest: includesInterest,
                    removed_violations: removedViolations
                };
                
                // Submit AJAX request
                submitAdjudication(requestData, ticketId);
            }
        });
    }
    
    // Separate function to handle the AJAX submission and response
    function submitAdjudication(requestData, ticketId) {
        fetch('/adjudication/ticket/adjudicate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                // Check if adjudication might have succeeded despite the error
                return checkAdjudicationStatus(ticketId).then(wasProcessed => {
                    if (wasProcessed) {
                        return {
                            status: 'success',
                            ticket_id: ticketId,
                            adjudicated_by: 'Current User',
                            was_verified: true
                        };
                    }
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                handleSuccessfulAdjudication(data, ticketId, requestData);
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'An error occurred while processing the adjudication.',
                    confirmButtonColor: 'var(--primary-color)'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error Submitting Adjudication',
                html: `
                    <p>${error.message || 'An unexpected error occurred'}</p>
                    <p class="mt-2 text-muted small">If the problem persists, please contact the system administrator.</p>
                `,
                confirmButtonColor: 'var(--primary-color)'
            });
        });
    }
    
    // Handle successful adjudication
    function handleSuccessfulAdjudication(data, ticketId, requestData) {
        Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: data.was_verified ? 
                'Adjudication was processed successfully after verification.' :
                'Adjudication decision has been submitted successfully.',
            confirmButtonColor: 'var(--primary-color)'
        }).then(() => {
            // Update UI with the successful adjudication
            updateAdjudicationUI(data, ticketId, requestData);
        });
    }
    
    // Update UI after successful adjudication
    function updateAdjudicationUI(data, ticketId, requestData) {
        // Find the violation card and adjudicated table
        const violationCard = document.querySelector(`.violation-card[data-violation-id="${ticketId}"]`);
        let adjudicatedTableBody = document.getElementById('adjudicatedViolationsBody');
            
        // Create new row in adjudicated table
        addAdjudicatedTableRow(data, ticketId, requestData, adjudicatedTableBody);
        
        // Remove the card from pending list
        if (violationCard) {
            violationCard.style.animation = 'fadeOutCard 0.3s ease forwards';
            
            setTimeout(() => {
                violationCard.remove();
                updateCountsAndUI();
                
                // Reset the form
                document.getElementById('noViolationSelectedMessage').style.display = 'block';
                document.getElementById('adjudicationFormContent').style.display = 'none';
                document.getElementById('adjudicationForm').reset();
            }, 300);
        }
    }
    
    // Add new row to the adjudicated table
    function addAdjudicatedTableRow(data, ticketId, requestData, adjudicatedTableBody) {
        const {
            violation_types: selectedTypes,
            penalty_amount: penaltyAmount,
            interest_amount: interestAmount,
            total_with_interest: totalWithInterest
        } = requestData;
        
        // Format date
        const formattedDate = data.adjudication_date ? 
            new Date(data.adjudication_date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }) : new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        
        // Create the new row
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>${ticketId}</td>
            <td>${formattedDate}</td>
            <td class="adjudicated-violation-types" data-violation-types='${JSON.stringify(selectedTypes)}'>${selectedTypes.join(', ')}</td>
            <td>₱${parseFloat(penaltyAmount).toFixed(2)}</td>
            <td class="${interestAmount > 0 ? 'text-danger fw-semibold' : ''}">
                ${interestAmount > 0 ? '₱' + interestAmount.toFixed(2) : '-'}
            </td>
            <td class="fw-semibold">
                ${interestAmount > 0 ? '₱' + totalWithInterest.toFixed(2) : '-'}
            </td>
            <td>${data.adjudicated_by || 'Current User'}</td>
            <td><span class="badge ${data.status === 'APPROVED' ? 'bg-success' : 'bg-primary'} text-white">${data.status || 'ADJUDICATED'}</span></td>
        `;
        
        // Add the row to the table
        if (adjudicatedTableBody) {
            adjudicatedTableBody.prepend(newRow);
            newRow.style.animation = 'highlightNewRow 3s';
            
            // Show success toast message
            showSuccessToast();
            
            // Scroll to the new row
            setTimeout(() => {
                newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    }
    
    // Update counts and UI elements
    function updateCountsAndUI() {
        // Update counts
        const pendingCount = document.querySelectorAll('.violation-card').length;
        const adjudicatedCount = document.querySelectorAll('#adjudicatedViolationsBody tr').length;
        
        // Update badge counts
        const pendingCountElement = document.querySelector('.card-header .badge.bg-primary');
        const adjudicatedCountElement = document.querySelector('.card-header .badge.bg-success');
        
        if (pendingCountElement) pendingCountElement.textContent = pendingCount;
        if (adjudicatedCountElement) adjudicatedCountElement.textContent = adjudicatedCount;
        
        // Update headers
        const pendingHeader = document.querySelector('.card-header h5');
        const adjudicatedHeader = document.querySelector('.card:last-child .card-header h5');
        
        if (pendingHeader) pendingHeader.textContent = `Pending Violations (${pendingCount})`;
        if (adjudicatedHeader) adjudicatedHeader.textContent = 'Adjudicated Violations';
        
        // Show message if all violations are adjudicated
        if (pendingCount === 0) {
            document.getElementById('pendingViolationsContainer').innerHTML = `
                <div class="alert alert-success">
                    <div class="d-flex align-items-center">
                        <span class="material-icons me-2">check_circle</span>
                        <p class="mb-0">All violations have been adjudicated.</p>
                    </div>
                </div>
            `;
        }
        
        // Check if adjudicated table was empty and update UI if needed
        const noAdjudicationsMessage = document.querySelector('.card-body:last-child .alert-info');
        if (noAdjudicationsMessage && noAdjudicationsMessage.textContent.includes('No adjudicated violations')) {
            noAdjudicationsMessage.remove();
            
            // Add table structure
            createAdjudicatedTable();
        }
    }
    
    // Create adjudicated table if it doesn't exist
    function createAdjudicatedTable() {
        const tableContainer = document.querySelector('.card-body:last-child');
        if (!tableContainer.querySelector('.table-responsive')) {
            tableContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Ticket #</th>
                                <th>Date Adjudicated</th>
                                <th>Violation Types</th>
                                <th>Penalty</th>
                                <th>Interest</th>
                                <th>Total</th>
                                <th>Adjudicated By</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="adjudicatedViolationsBody">
                        </tbody>
                    </table>
                </div>
            `;
        }
    }
    
    // Show success toast message
    function showSuccessToast() {
        const adjudicatedCard = document.querySelector('.card:last-child');
        if (adjudicatedCard) {
            const toast = document.createElement('div');
            toast.className = 'alert alert-success position-absolute';
            toast.style.top = '0';
            toast.style.right = '1rem';
            toast.style.zIndex = '100';
            toast.style.maxWidth = '300px';
            toast.style.animation = 'pulseMessage 2s infinite';
            toast.style.border = 'none';
            toast.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            toast.innerHTML = `
                <div class="d-flex align-items-center">
                    <span class="material-icons me-2">check_circle</span>
                    <div>
                        <p class="mb-0">Adjudication added successfully</p>
                    </div>
                </div>
            `;
            
            adjudicatedCard.style.position = 'relative';
            adjudicatedCard.appendChild(toast);
            
            // Remove toast after 3 seconds
            setTimeout(() => {
                toast.style.transition = 'all 0.5s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        }
    }
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}); 
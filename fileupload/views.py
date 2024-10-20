import pandas as pd
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from .forms import FileUploadForm
from datetime import datetime

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploaded_file = request.FILES['file']
                if uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    return render(request, 'upload.html', {
                        'form': form, 
                        'error': 'Please upload an Excel or CSV file'
                    })
                
                summary, total_dpd = generate_summary(df)
                
                
                unique_states_count = len(set(item['state'] for item in summary))
                
                send_summary_email(summary)

                return render(request, 'summary.html', {
                    'summary': summary,
                    'total_dpd': total_dpd,
                    'unique_states_count': unique_states_count  
                })
                
            except Exception as e:
                return render(request, 'upload.html', {
                    'form': form, 
                    'error': f'Error processing file: {str(e)}'
                })
    else:
        form = FileUploadForm()
    
    return render(request, 'upload.html', {'form': form})


def generate_summary(df):
    summary_df = df.groupby(['Cust State', 'Cust Pin'])['DPD'].agg(['count']).reset_index()
    
    summary_data = []
    for _, row in summary_df.iterrows():
        summary_data.append({
            'state': row['Cust State'],
            'pin': row['Cust Pin'],
            'dpd': row['count']
        })
    
    total_dpd = sum(item['dpd'] for item in summary_data)
    
    return summary_data, total_dpd

def send_summary_email(summary_data):
    current_date = datetime.now().strftime("%d-%m-%Y")
    subject = f'Python Assignment - Venuchander - {current_date}'

    
    header = "=== Summary Report ===\n"
    header += f"Date: {current_date}\n"
    header += "=" * 30 + "\n"

    
    table_header = f"{'State':<30} {'Pin Code':<15} {'DPD':<10}\n"
    table_header += "=" * 70 + "\n"

    
    rows = []
    total_dpd = 0
    state_counts = {}

    for item in summary_data:
        state = item['state']
        if state not in state_counts:
            state_counts[state] = {'count': 0, 'total_dpd': 0}
        state_counts[state]['count'] += 1
        state_counts[state]['total_dpd'] += item['dpd']
        total_dpd += item['dpd']

        rows.append(f"{item['state']:<30} {item['pin']:<15} {item['dpd']:<10}")

    
    statistics = "\n=== Summary Statistics ===\n"
    statistics += "=" * 30 + "\n"
    statistics += f"Total Records:               **{len(summary_data)}**\n"
    statistics += f"Total DPD:                   **{total_dpd}**\n"
    statistics += f"Number of Unique States:     **{len(state_counts)}**\n\n"

    
    statistics += "=== State-wise Breakdown ===\n"
    statistics += "=" * 70 + "\n"
    statistics += f"{'State':<30} {'Records':<15} {'Total DPD':<15}\n"
    statistics += "=" * 70 + "\n"

    for state, data in sorted(state_counts.items()):
        statistics += f"{state:<30} {data['count']:<15} {data['total_dpd']:<15}\n"

    
    message = (
        header +
        table_header +
        "\n".join(rows) +
        "\n" + "=" * 70 + "\n" +
        statistics +
        "\n\nThis is an automated report generated from the file upload system."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['tech@themedius.ai'],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

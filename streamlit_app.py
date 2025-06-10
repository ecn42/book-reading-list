import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from typing import Optional
import numpy as np
from io import BytesIO

# Configure Streamlit
st.set_page_config(
    layout="wide",
    page_title="📚 Book Reading Dashboard",
    page_icon="📚",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86AB;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
    }
    .help-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
@st.cache_data
def create_template_data():
    """Create template data as a DataFrame."""
    template_data = {
        'BOOK': [
            'The Great Gatsby',
            'To Kill a Mockingbird',
            '1984',
            'Pride and Prejudice',
            'The Catcher in the Rye',
            'Lord of the Flies',
            'Dune',
            'The Hobbit',
            'Fahrenheit 451',
            'Brave New World',
            'The Lord of the Rings',
            'Harry Potter and the Philosopher\'s Stone'
        ],
        'AUTHOR': [
            'F. Scott Fitzgerald',
            'Harper Lee',
            'George Orwell',
            'Jane Austen',
            'J.D. Salinger',
            'William Golding',
            'Frank Herbert',
            'J.R.R. Tolkien',
            'Ray Bradbury',
            'Aldous Huxley',
            'J.R.R. Tolkien',
            'J.K. Rowling'
        ],
        'WORDS': [47094, 100388, 88942, 122189, 73404, 59900, 187240, 95022, 46118, 63766, 473000, 77325],
        'YEAR': [2022, 2022, 2022, 2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024, 2024],
        'GENRE': ['Fiction', 'Fiction', 'Dystopian', 'Romance', 'Fiction', 'Fiction', 'Science Fiction', 'Fantasy', 'Dystopian', 'Dystopian', 'Fantasy', 'Fantasy']
    }
    
    return pd.DataFrame(template_data)

@st.cache_data
def create_template_excel():
    """Create a template Excel file with sample data."""
    df = create_template_data()
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Books')
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Books']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output.getvalue()

@st.cache_data
def load_and_validate_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Load and validate the Excel file."""
    try:
        df = pd.read_excel(uploaded_file)
        
        required_columns = ['BOOK', 'AUTHOR', 'WORDS', 'YEAR', 'GENRE']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return None
        
        # Data type conversion with error handling
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        df['WORDS'] = pd.to_numeric(df['WORDS'], errors='coerce')
        df['GENRE'] = df['GENRE'].astype(str)
        df['BOOK'] = df['BOOK'].astype(str)
        df['AUTHOR'] = df['AUTHOR'].astype(str)
        
        # Remove rows with invalid data
        initial_rows = len(df)
        df = df.dropna(subset=['YEAR', 'WORDS'])
        
        if len(df) < initial_rows:
            st.warning(f"⚠️ Removed {initial_rows - len(df)} rows with invalid data")
        
        # Calculate pages (assuming 300 words per page)
        df['PAGES'] = (df['WORDS'] / 300).round(0)
        
        # Add original order index to preserve order
        df = df.reset_index(drop=True)
        df['ORIGINAL_ORDER'] = df.index
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        return None

def process_template_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process template data the same way as uploaded data."""
    # Data type conversion
    df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
    df['WORDS'] = pd.to_numeric(df['WORDS'], errors='coerce')
    df['GENRE'] = df['GENRE'].astype(str)
    df['BOOK'] = df['BOOK'].astype(str)
    df['AUTHOR'] = df['AUTHOR'].astype(str)
    
    # Calculate pages (assuming 300 words per page)
    df['PAGES'] = (df['WORDS'] / 300).round(0)
    
    # Add original order index to preserve order
    df = df.reset_index(drop=True)
    df['ORIGINAL_ORDER'] = df.index
    
    return df

def create_color_palette(n_colors: int) -> list:
    """Generate a consistent color palette."""
    return sns.color_palette("husl", n_colors).as_hex()

@st.cache_data
def plot_book_stack(df: pd.DataFrame):
    """Create an improved book stack visualization maintaining original order."""
    # Keep original order instead of sorting
    df_plot = df.copy().sort_values('ORIGINAL_ORDER')
    
    # Create figure with transparent background
    fig, ax = plt.subplots(figsize=(14, 10))
    
    year_heights = {}
    years = sorted(df_plot['YEAR'].unique())
    colors = create_color_palette(len(df_plot))
    
    for idx, (_, row) in enumerate(df_plot.iterrows()):
        year = row['YEAR']
        pages = row['PAGES']
        title = row['BOOK']
        
        current_height = year_heights.get(year, 0)
        year_idx = years.index(year)
        
        # Book dimensions
        width = 0.7
        height = max(pages * 0.01, 0.5)  # Minimum height for visibility
        
        # Create rectangle
        rect = patches.Rectangle(
            (year_idx - width/2, current_height),
            width, height,
            facecolor=colors[idx % len(colors)],
            edgecolor='white',
            linewidth=0.5,
            alpha=0.8
        )
        ax.add_patch(rect)
        
        # Add text if book is large enough
        if height > 1:
            text = title[:20] + "..." if len(title) > 20 else title
            ax.text(
                year_idx, current_height + height/2, text,
                ha='center', va='center',
                fontsize=8, color='white',
                weight='bold'
            )
        
        year_heights[year] = current_height + height
    
    # Styling
    max_height = max(year_heights.values()) if year_heights else 10
    ax.set_xlim(-0.5, len(years) - 0.5)
    ax.set_ylim(0, max_height * 1.1)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, fontsize=12)
    ax.set_xlabel("Year", fontsize=14, weight='bold')
    ax.set_title("Book Stack by Year", fontsize=16, weight='bold', pad=20)
    
    # Remove y-axis and add subtle grid
    ax.yaxis.set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return fig

@st.cache_data
def plot_genre_distribution(df: pd.DataFrame):
    """Create genre distribution plots."""
    # Create figure with transparent background
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Books by genre per year (stacked bar)
    genre_year = df.groupby(['YEAR', 'GENRE']).size().unstack(fill_value=0)
    colors = create_color_palette(len(genre_year.columns))
    
    genre_year.plot(
        kind='bar', stacked=True, ax=ax1,
        color=colors, alpha=0.8
    )
    
    ax1.set_title("Books by Genre per Year", fontsize=14, weight='bold')
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Number of Books", fontsize=12)
    ax1.legend(title="Genre", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.tick_params(axis='x', rotation=45)
    
    # Overall genre distribution (pie chart)
    genre_counts = df['GENRE'].value_counts()
    ax2.pie(
        genre_counts.values, labels=genre_counts.index,
        autopct='%1.1f%%', startangle=90,
        colors=colors[:len(genre_counts)]
    )
    ax2.set_title("Overall Genre Distribution", fontsize=14, weight='bold')
    
    plt.tight_layout()
    return fig

@st.cache_data
def plot_author_stats(df: pd.DataFrame):
    """Create author statistics visualization."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Top authors by number of books
    author_counts = df['AUTHOR'].value_counts().head(10)
    colors = create_color_palette(len(author_counts))
    
    author_counts.plot(kind='barh', ax=ax1, color=colors, alpha=0.8)
    ax1.set_title("Top 10 Authors by Number of Books", fontsize=14, weight='bold')
    ax1.set_xlabel("Number of Books", fontsize=12)
    ax1.set_ylabel("Author", fontsize=12)
    
    # Top authors by total pages read
    author_pages = df.groupby('AUTHOR')['PAGES'].sum().sort_values(ascending=False).head(10)
    
    author_pages.plot(kind='barh', ax=ax2, color=colors[:len(author_pages)], alpha=0.8)
    ax2.set_title("Top 10 Authors by Total Pages Read", fontsize=14, weight='bold')
    ax2.set_xlabel("Total Pages", fontsize=12)
    ax2.set_ylabel("Author", fontsize=12)
    
    plt.tight_layout()
    return fig

def display_metrics(df: pd.DataFrame):
    """Display key reading metrics."""
    total_books = len(df)
    total_pages = df['PAGES'].sum()
    avg_pages = df['PAGES'].mean()
    years_active = df['YEAR'].nunique()
    unique_authors = df['AUTHOR'].nunique()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📚 Total Books", f"{total_books:,}")
    with col2:
        st.metric("📄 Total Pages", f"{total_pages:,.0f}")
    with col3:
        st.metric("📊 Avg Pages/Book", f"{avg_pages:.0f}")
    with col4:
        st.metric("📅 Years Active", years_active)
    with col5:
        st.metric("✍️ Unique Authors", unique_authors)

def display_summaries(df: pd.DataFrame):
    """Display data summaries in organized tabs."""
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Yearly Summary", "📚 Genre Summary", "✍️ Author Summary", "📊 Detailed Breakdown"])
    
    with tab1:
        yearly_summary = df.groupby('YEAR').agg({
            'BOOK': 'count',
            'PAGES': ['sum', 'mean'],
            'GENRE': 'nunique',
            'AUTHOR': 'nunique'
        }).round(1)
        
        yearly_summary.columns = ['Books Read', 'Total Pages', 'Avg Pages', 'Genres', 'Authors']
        st.dataframe(yearly_summary, use_container_width=True)
    
    with tab2:
        genre_summary = df.groupby('GENRE').agg({
            'BOOK': 'count',
            'PAGES': 'sum',
            'AUTHOR': 'nunique'
        }).sort_values('BOOK', ascending=False)
        
        genre_summary.columns = ['Books Read', 'Total Pages', 'Unique Authors']
        st.dataframe(genre_summary, use_container_width=True)
    
    with tab3:
        author_summary = df.groupby('AUTHOR').agg({
            'BOOK': 'count',
            'PAGES': 'sum',
            'GENRE': 'nunique',
            'YEAR': lambda x: ', '.join(map(str, sorted(x.unique())))
        }).sort_values('BOOK', ascending=False)
        
        author_summary.columns = ['Books Read', 'Total Pages', 'Genres', 'Years Read']
        st.dataframe(author_summary, use_container_width=True)
    
    with tab4:
        for year in sorted(df['YEAR'].unique(), reverse=True):
            with st.expander(f"📅 {int(year)} Details"):
                year_data = df[df['YEAR'] == year].sort_values('ORIGINAL_ORDER')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Books by Genre:**")
                    genre_counts = year_data['GENRE'].value_counts()
                    st.dataframe(genre_counts.to_frame('Count'))
                
                with col2:
                    st.write("**Books by Author:**")
                    author_counts = year_data['AUTHOR'].value_counts()
                    st.dataframe(author_counts.to_frame('Count'))
                
                with col3:
                    st.write("**Summary Stats:**")
                    stats_data = {
                        'Total Books': [len(year_data)],
                        'Total Pages': [year_data['PAGES'].sum()],
                        'Unique Authors': [year_data['AUTHOR'].nunique()],
                        'Unique Genres': [year_data['GENRE'].nunique()]
                    }
                    stats_df = pd.DataFrame(stats_data).T
                    stats_df.columns = ['Value']
                    st.dataframe(stats_df, use_container_width=True)
                
                st.write("**Book List (Original Order):**")
                book_list = year_data[['BOOK', 'AUTHOR', 'PAGES', 'GENRE']]
                st.dataframe(book_list, use_container_width=True)

# Main Application
def main():
    st.markdown('<h1 class="main-header">📚 Book Reading Dashboard</h1>', unsafe_allow_html=True)
    
    # Load template data by default
    template_df = create_template_data()
    processed_template_df = process_template_data(template_df)
    
    # Initialize session state for data
    if 'current_df' not in st.session_state:
        st.session_state.current_df = processed_template_df
        st.session_state.data_source = "template"
    
    # Sidebar for file upload and filters
    # Sidebar for file upload and filters
    with st.sidebar:
        # Help Section
        with st.expander("❓ How to Use This Dashboard", expanded=False):
            st.markdown("""
            ### 📖 **Getting Started**
            1. **Download the template** below to see the required format
            2. **Fill in your book data** in the Excel file
            3. **Upload your file** and explore your reading statistics!
            
            ### 📊 **Required Data Columns**
            - **BOOK**: The title of the book
            - **AUTHOR**: The author's name
            - **WORDS**: Total word count of the book
            - **YEAR**: The year you read the book
            - **GENRE**: The book's genre (Fiction, Non-fiction, etc.)
            
            ### 🔍 **Finding Word Counts**
            **Don't know the word count?** Try these methods:
            - **Google Search**: Search "[book title] word count"
            - **Goodreads**: Often lists word counts in book details
            - **Publisher websites**: Sometimes include this information
            - **Reading databases**: Sites like "How Long to Read" provide estimates
            - **Rule of thumb**: Average novel ≈ 70,000-90,000 words
            
            ### 📄 **Page Calculations**
            - **Standard used**: 300 words per page (industry average)
            - **Why 300?**: This is a common publishing standard for novels
            - **Note**: Actual pages vary by font size, margins, and formatting
            - **Academic books**: Often have fewer words per page (~250)
            - **Children's books**: Usually have much fewer words per page
            
            ### 🎯 **Dashboard Features**
            - **Key Metrics**: Overview of your reading habits
            - **Visualizations**: 
            - Genre distribution over time
            - Book stack visualization by year
            - Author statistics and comparisons
            - **Filters**: Filter by year, genre, or author
            - **Summaries**: Detailed breakdowns by year, genre, and author
            
            ### 💡 **Tips for Best Results**
            - **Be consistent** with genre naming (e.g., always use "Science Fiction" not "Sci-Fi")
            - **Use full author names** for better statistics
            - **Double-check word counts** for accuracy
            - **Include all books** you've read, even short ones
            - **Update regularly** to track your reading progress
            
            ### 🚀 **Pro Tips**
            - Use the **filters** to analyze specific time periods or genres
            - Check the **Author Summary** to see your most-read authors
            - The **Book Stack** visualization shows reading volume by year
            - **Export your data** regularly as a backup
            """)
        
        st.markdown("---")
        
        st.header("📁 Data Upload")
        
        # Template download section
        st.subheader("📋 Download Template")
        st.write("Need a template? Download the Excel template below:")
        
        template_excel = create_template_excel()
        st.download_button(
            label="📥 Download Excel Template",
            data=template_excel,
            file_name="book_reading_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download this template and fill it with your book data"
        )
        
        st.markdown("---")
        
        # File upload section
        uploaded_file = st.file_uploader(
            "Upload your Excel file",
            type=['xlsx', 'xls'],
            help="File should contain columns: BOOK, AUTHOR, WORDS, YEAR, GENRE"
        )
        
        # Process uploaded file
        if uploaded_file is not None:
            df = load_and_validate_data(uploaded_file)
            if df is not None:
                st.session_state.current_df = df
                st.session_state.data_source = "uploaded"
        
        # Show current data source AFTER processing upload
        if st.session_state.data_source == "template":
            st.info("📋 Currently showing example template data")
        else:
            st.success("✅ Using your uploaded data")
            if st.button("🔄 Reset to Template Data"):
                st.session_state.current_df = processed_template_df
                st.session_state.data_source = "template"
                st.rerun()
        
        # Use current dataframe
        df = st.session_state.current_df
        
        # Filters
        st.header("🔍 Filters")
        years = sorted(df['YEAR'].unique())
        selected_years = st.multiselect(
            "Select Years",
            years,
            default=years
        )
        
        genres = sorted(df['GENRE'].unique())
        selected_genres = st.multiselect(
            "Select Genres",
            genres,
            default=genres
        )
        
        authors = sorted(df['AUTHOR'].unique())
        selected_authors = st.multiselect(
            "Select Authors",
            authors,
            default=authors
        )
        
        # Apply filters
        if selected_years and selected_genres and selected_authors:
            df = df[
                (df['YEAR'].isin(selected_years)) &
                (df['GENRE'].isin(selected_genres)) &
                (df['AUTHOR'].isin(selected_authors))
            ]
    
    # Main content
    if df is not None and not df.empty:
        # Key metrics
        st.header("📊 Key Metrics")
        display_metrics(df)
        
        st.divider()
        
        # Visualizations
        st.header("📈 Visualizations")
        
        with st.container():
            fig1 = plot_genre_distribution(df)
            st.pyplot(fig1, use_container_width=True, transparent=False)
    
        with st.container():
            fig2 = plot_book_stack(df)
            st.pyplot(fig2, use_container_width=True, transparent=False)
        
        with st.container():
            fig3 = plot_author_stats(df)
            st.pyplot(fig3, use_container_width=True, transparent=False)
    
        st.divider()
        
        # Data summaries
        st.header("📋 Data Summaries")
        display_summaries(df)
        
        # Raw data view
        with st.expander("🔍 View Raw Data"):
            # Show data in original order
            display_df = df.sort_values('ORIGINAL_ORDER')[['BOOK', 'AUTHOR', 'WORDS', 'PAGES', 'YEAR', 'GENRE']]
            st.dataframe(display_df, use_container_width=True)
    
    elif df is not None and df.empty:
        st.warning("⚠️ No data remaining after filtering. Please adjust your filters.")
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "📚 Happy Reading! Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
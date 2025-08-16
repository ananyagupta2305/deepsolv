
import streamlit as st
import requests
import json
from datetime import datetime
import time

st.set_page_config(
    page_title="Shopify Store Insights Fetcher",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'last_analyzed_url' not in st.session_state:
    st.session_state.last_analyzed_url = ""
if 'analysis_timestamp' not in st.session_state:
    st.session_state.analysis_timestamp = None

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .competitor-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .product-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .success-alert {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-alert {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .info-alert {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    
    .stExpander > details > summary {
        background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 8px;
        padding: 1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation and settings
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331970.png", width=100)
    st.title("🛍️ Shopify Insights")
    
    # Show current analysis status
    if st.session_state.analysis_data:
        st.markdown('<div class="info-alert">✅ <strong>Data Available</strong><br>Analysis ready for viewing</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Current Analysis"):
            st.session_state.analysis_data = None
            st.session_state.last_analyzed_url = ""
            st.session_state.analysis_timestamp = None
            st.rerun()
    
    # Quick examples
    st.subheader("📝 Quick Examples")
    example_stores = {
        "ColourPop Cosmetics": "https://colourpop.com",
        "Gymshark": "https://gymshark.com",
        "CUPSHE": "https://cupshe.com"
    }
    
    selected_example = st.selectbox("Select an example store:", [""] + list(example_stores.keys()))
    
    # Recent searches (mock data for demo)
    st.subheader("🕒 Recent Searches")
    recent_searches = [
        "colourpop.com - 2 hours ago",
        "fashionnova.com - 1 day ago", 
        "gymshark.com - 3 days ago"
    ]
    
    for search in recent_searches:
        st.text(f"• {search}")

# Main header
st.markdown("""
<div class="main-header">
    <h1>🛍️ Shopify Store Insights Fetcher</h1>
    <p>Extract comprehensive brand insights from any Shopify store</p>
</div>
""", unsafe_allow_html=True)

# Input section
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    url_input = st.text_input(
        "🌐 Enter Shopify Store URL:",
        value=example_stores.get(selected_example, ""),
        placeholder="https://example-store.com",
        help="Enter the complete URL of the Shopify store you want to analyze"
    )

with col2:
    include_comp = st.checkbox(
        "🏆 Include Competitor Analysis",
        value=False,
        help="This will find and analyze competitor stores (takes longer)"
    )

with col3:
    st.write("")  # Spacing
    st.write("")  # Spacing
    fetch_button = st.button(
        "🚀 Fetch Insights",
        type="primary",
        use_container_width=True
    )

# Show analysis notice if data exists for different URL
if st.session_state.analysis_data and url_input != st.session_state.last_analyzed_url and url_input:
    st.warning(f"💡 You have existing analysis data for: **{st.session_state.last_analyzed_url}**. Click 'Fetch Insights' to analyze the new URL or clear the current analysis from the sidebar.")

# Validation
if fetch_button and not url_input:
    st.markdown('<div class="error-alert">⚠️ Please enter a store URL to continue</div>', unsafe_allow_html=True)
    st.stop()

# Main processing
if fetch_button and url_input:
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Initial request
        status_text.text("🔍 Analyzing store structure...")
        progress_bar.progress(20)
        
        response = requests.post(
            "http://127.0.0.1:8000/insights",
            json={"website_url": url_input.strip(), "include_competitors": include_comp},
            timeout=120  # Increased timeout for competitor analysis
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        if response.status_code == 200:
            # Store data in session state
            st.session_state.analysis_data = response.json()
            st.session_state.last_analyzed_url = url_input.strip()
            st.session_state.analysis_timestamp = datetime.now()
            
            st.success("✅ Analysis completed successfully! Data has been stored and will persist during your session.")
            
        else:
            error_detail = response.json().get('detail', 'Unknown error occurred')
            st.markdown(f'<div class="error-alert">❌ Error {response.status_code}: {error_detail}</div>', unsafe_allow_html=True)
            
            # Provide helpful suggestions based on error
            if response.status_code == 404:
                st.info("💡 **Suggestions:**\n- Check if the URL is correct\n- Ensure the website is accessible\n- Try adding 'https://' prefix")
            elif response.status_code == 500:
                st.info("💡 **Suggestions:**\n- The website might be blocking automated requests\n- Try again in a few minutes\n- Contact support if the issue persists")

    except requests.exceptions.Timeout:
        st.markdown('<div class="error-alert">⏰ Request timed out. The analysis is taking longer than expected. Please try again.</div>', unsafe_allow_html=True)
    except requests.exceptions.ConnectionError:
        st.markdown('<div class="error-alert">🔌 Connection failed. Make sure the FastAPI server is running at http://127.0.0.1:8000</div>', unsafe_allow_html=True)
        st.info("💡 **To start the server:**\n```bash\npython -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload\n```")
    except Exception as e:
        st.markdown(f'<div class="error-alert">💥 Unexpected error: {str(e)}</div>', unsafe_allow_html=True)

# Display results if data exists in session state
if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    brand = data["brand"]
    
    # Show analysis info
    analysis_time = st.session_state.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.analysis_timestamp else "Unknown"
    st.markdown(f'<div class="success-alert">📊 <strong>Showing analysis for:</strong> {st.session_state.last_analyzed_url}<br><small>Analyzed on: {analysis_time}</small></div>', unsafe_allow_html=True)
    
    # Brand overview metrics
    st.subheader("📊 Brand Overview")
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric(
            "Products Found",
            len(brand["products"]),
            delta=f"+{len(brand['hero_products'])} featured"
        )
    with metric_cols[1]:
        st.metric(
            "FAQs Extracted",
            len(brand["faqs"]),
            delta="questions"
        )
    with metric_cols[2]:
        st.metric(
            "Social Channels",
            len(brand["social_handles"]),
            delta="platforms"
        )
    with metric_cols[3]:
        contact_count = len(brand["contact_info"]["emails"]) + len(brand["contact_info"]["phones"])
        st.metric(
            "Contact Methods",
            contact_count,
            delta="available"
        )
    
    # Main brand section
    st.header(f"🏪 {brand['brand_name']}")
    st.markdown(f"**Website:** [{brand['website']}]({brand['website']})")
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛍️ Products", "📋 Policies & FAQs", "📞 Contact & Social", 
        "📖 Brand Info", "🔗 Important Links"
    ])
    
    # Tab 1: Products
    with tab1:
        st.subheader("⭐ Featured Products")
        if brand["hero_products"]:
            hero_cols = st.columns(min(len(brand["hero_products"]), 4))
            for i, product in enumerate(brand["hero_products"][:8]):
                with hero_cols[i % 4]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{product.get('image', 'https://via.placeholder.com/150')}" 
                             style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px;">
                        <h4 style="margin: 8px 0 4px 0; font-size: 14px;">{product['title'][:50]}{'...' if len(product['title']) > 50 else ''}</h4>
                        <p style="color: #28a745; font-weight: bold; margin: 0;">💰 ${product['price']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.subheader("📦 Full Product Catalog")
        if brand["products"]:
            # Product search and filter
            search_term = st.text_input("🔍 Search products:", placeholder="Search by product name...")
            
            # Filter products based on search
            filtered_products = brand["products"]
            if search_term:
                filtered_products = [p for p in brand["products"] 
                                   if search_term.lower() in p['title'].lower()]
            
            st.info(f"Showing {len(filtered_products)} of {len(brand['products'])} products")
            
            # Display filtered products in a more compact grid
            products_per_row = 6
            for i in range(0, len(filtered_products), products_per_row):
                cols = st.columns(products_per_row)
                for j, product in enumerate(filtered_products[i:i+products_per_row]):
                    with cols[j]:
                        if product.get("image"):
                            st.image(product["image"], width=100)
                        st.markdown(f"**{product['title'][:30]}{'...' if len(product['title']) > 30 else ''}**")
                        st.markdown(f"💰 ${product['price']}")
        
    # Tab 2: Policies & FAQs
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🛡️ Store Policies")
            
            if brand["privacy_policy"]:
                with st.expander("🔒 Privacy Policy", expanded=False):
                    st.markdown(f"[📄 View Full Policy]({brand['privacy_policy']['url']})")
                    if brand["privacy_policy"]["content"]:
                        st.write(brand["privacy_policy"]["content"][:500] + "..." if len(brand["privacy_policy"]["content"]) > 500 else brand["privacy_policy"]["content"])
            
            if brand["return_refund_policy"]:
                with st.expander("↩️ Return & Refund Policy", expanded=False):
                    st.markdown(f"[📄 View Full Policy]({brand['return_refund_policy']['url']})")
                    if brand["return_refund_policy"]["content"]:
                        st.write(brand["return_refund_policy"]["content"][:500] + "..." if len(brand["return_refund_policy"]["content"]) > 500 else brand["return_refund_policy"]["content"])
        
        with col2:
            st.subheader("❓ Frequently Asked Questions")
            
            if brand.get("faqs"):
                for i, faq in enumerate(brand["faqs"][:10]):
                    with st.expander(f"Q{i+1}: {faq['question']}", expanded=False):
                        st.write(f"**Answer:** {faq['answer']}")
            else:
                st.info("No FAQs found on this store.")
    
    # Tab 3: Contact & Social
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📞 Contact Information")
            
            if brand["contact_info"]["emails"]:
                st.markdown("**📧 Email Addresses:**")
                for email in brand["contact_info"]["emails"]:
                    st.markdown(f"• [{email}](mailto:{email})")
            
            if brand["contact_info"]["phones"]:
                st.markdown("**📱 Phone Numbers:**")
                for phone in brand["contact_info"]["phones"]:
                    st.markdown(f"• {phone}")
            
            if not brand["contact_info"]["emails"] and not brand["contact_info"]["phones"]:
                st.info("No direct contact information found.")
        
        with col2:
            st.subheader("🌐 Social Media Presence")
            
            if brand["social_handles"]:
                for social in brand["social_handles"]:
                    platform_icons = {
                        "Instagram": "📷",
                        "Facebook": "📘",
                        "Twitter": "🐦",
                        "TikTok": "🎵",
                        "YouTube": "📺",
                        "LinkedIn": "💼",
                        "Pinterest": "📌"
                    }
                    icon = platform_icons.get(social['platform'], "🔗")
                    st.markdown(f"{icon} **{social['platform']}:** [{social['url']}]({social['url']})")
            else:
                st.info("No social media handles found.")
    
    # Tab 4: Brand Info
    with tab4:
        st.subheader("📖 About the Brand")
        st.write(brand["about_brand"])
        
        # Display brand insights in a nice format
        if brand.get("additional_insights"):
            st.subheader("💡 Additional Insights")
            insights_cols = st.columns(2)
            for i, (key, value) in enumerate(brand["additional_insights"].items()):
                with insights_cols[i % 2]:
                    status = "✅" if value else "❌"
                    st.markdown(f"{status} **{key.replace('_', ' ').title()}**")
    
    # Tab 5: Important Links
    with tab5:
        st.subheader("🔗 Important Store Links")
        
        if brand["important_links"]:
            links_cols = st.columns(2)
            for i, (key, link) in enumerate(brand["important_links"].items()):
                with links_cols[i % 2]:
                    link_icons = {
                        "contact_us": "📞",
                        "order_tracking": "📦",
                        "blog": "📝",
                        "shipping": "🚚",
                        "size_guide": "📏"
                    }
                    icon = link_icons.get(key, "🔗")
                    st.markdown(f"{icon} **{key.replace('_', ' ').title()}:** [{link}]({link})")
        else:
            st.info("No additional important links found.")
    
    # Competitor Analysis Section
    if include_comp and data.get("competitors"):
        st.header("🏆 Competitor Analysis")
        st.info(f"Found {len(data['competitors'])} competitors for analysis")
        
        for i, comp in enumerate(data["competitors"]):
            with st.expander(f"🏪 Competitor {i+1}: {comp['brand_name']}", expanded=False):
                # Competitor metrics
                comp_cols = st.columns(4)
                with comp_cols[0]:
                    st.metric("Products", len(comp.get('products', [])))
                with comp_cols[1]:
                    st.metric("FAQs", len(comp.get('faqs', [])))
                with comp_cols[2]:
                    st.metric("Social Channels", len(comp.get('social_handles', [])))
                with comp_cols[3]:
                    contact_count = len(comp.get('contact_info', {}).get('emails', [])) + len(comp.get('contact_info', {}).get('phones', []))
                    st.metric("Contact Methods", contact_count)
                
                # Basic competitor info
                st.markdown(f"**Website:** [{comp['website']}]({comp['website']})")
                st.markdown(f"**About:** {comp.get('about_brand', 'N/A')[:200]}...")
                
                # Competitor products preview
                if comp.get('products'):
                    st.markdown("**Sample Products:**")
                    prod_cols = st.columns(min(len(comp['products']), 4))
                    for j, prod in enumerate(comp['products'][:4]):
                        with prod_cols[j]:
                            if prod.get('image'):
                                st.image(prod['image'], width=80)
                            st.caption(f"{prod['title'][:25]}...")
                            st.caption(f"💰 ${prod['price']}")
    
    # Download option
    st.subheader("💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Prepare data for download
        export_data = {
            "timestamp": st.session_state.analysis_timestamp.isoformat() if st.session_state.analysis_timestamp else datetime.now().isoformat(),
            "analyzed_url": st.session_state.last_analyzed_url,
            "brand_data": brand,
            "competitors": data.get("competitors", [])
        }
        
        st.download_button(
            label="📥 Download Full Report (JSON)",
            data=json.dumps(export_data, indent=2),
            file_name=f"{brand['brand_name']}_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            type="secondary",
            use_container_width=True
        )
    
    with col2:
        # Generate summary report
        timestamp_str = st.session_state.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.analysis_timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary = f"""BRAND INSIGHTS SUMMARY
=====================
Brand: {brand['brand_name']}
Website: {brand['website']}
Analysis Date: {timestamp_str}
Analyzed URL: {st.session_state.last_analyzed_url}

KEY METRICS:
- Total Products: {len(brand['products'])}
- Featured Products: {len(brand['hero_products'])}
- FAQs Available: {len(brand['faqs'])}
- Social Channels: {len(brand['social_handles'])}
- Contact Methods: {len(brand['contact_info']['emails']) + len(brand['contact_info']['phones'])}

COMPETITORS ANALYZED: {len(data.get('competitors', []))}

CONTACT INFORMATION:
- Emails: {', '.join(brand['contact_info']['emails']) if brand['contact_info']['emails'] else 'None found'}
- Phones: {', '.join(brand['contact_info']['phones']) if brand['contact_info']['phones'] else 'None found'}

SOCIAL MEDIA:
{chr(10).join([f"- {social['platform']}: {social['url']}" for social in brand['social_handles']]) if brand['social_handles'] else '- No social media found'}

ABOUT THE BRAND:
{brand['about_brand'][:500]}{'...' if len(brand['about_brand']) > 500 else ''}
"""
        
        st.download_button(
            label="📄 Download Summary (TXT)",
            data=summary,
            file_name=f"{brand['brand_name']}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            type="secondary",
            use_container_width=True
        )
    
    with col3:
        # Generate CSV of products
        if brand['products']:
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Product Title', 'Price', 'Image URL'])
            
            # Write product data
            for product in brand['products']:
                writer.writerow([
                    product.get('title', ''),
                    product.get('price', ''),
                    product.get('image', '')
                ])
            
            csv_data = output.getvalue()
            
            st.download_button(
                label="📊 Download Products (CSV)",
                data=csv_data,
                file_name=f"{brand['brand_name']}_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="secondary",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🛍️ <strong>Shopify Store Insights Fetcher</strong> - Powered by Advanced Web Scraping & AI</p>
    <p>Built with ❤️ using Streamlit, FastAPI, and LLM Processing</p>
    <p><small>Data persists throughout your session for seamless interaction</small></p>
</div>
""", unsafe_allow_html=True)
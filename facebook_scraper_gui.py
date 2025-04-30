import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import csv
from facebook_email_scraper import FacebookEmailScraper

class FacebookScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Email Scraper")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.setup_ui()
        self.is_scraping = False
        self.current_results = []
        
    def setup_ui(self):
        # Create frame for input
        input_frame = ttk.LabelFrame(self.root, text="Business Names (One per line)")
        input_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Text area for business names input
        self.business_names_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.business_names_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Buttons frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Load from file button
        self.load_file_btn = ttk.Button(
            button_frame, 
            text="Load Names from File", 
            command=self.load_from_file
        )
        self.load_file_btn.pack(side=tk.LEFT, padx=5)
        
        # Start scraping button
        self.start_btn = ttk.Button(
            button_frame, 
            text="Start Scraping", 
            command=self.start_scraping
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Save results button
        self.save_btn = ttk.Button(
            button_frame, 
            text="Save Results", 
            command=self.save_results,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress")
        progress_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100
        )
        self.progress_bar.pack(padx=10, pady=10, fill=tk.X)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(
            progress_frame, 
            textvariable=self.status_var
        )
        self.status_label.pack(padx=10, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.root, text="Results")
        results_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create Treeview for results
        columns = ("Business Name", "Email")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        self.results_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        # Configure grid weights
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def load_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Business Names File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    self.business_names_text.delete(1.0, tk.END)
                    self.business_names_text.insert(tk.INSERT, content)
                messagebox.showinfo("Success", f"Loaded {len(content.strip().split('\n'))} business names")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def start_scraping(self):
        if self.is_scraping:
            messagebox.showinfo("Info", "Scraping is already in progress")
            return
        
        # Get business names
        business_names = self.business_names_text.get(1.0, tk.END).strip()
        if not business_names:
            messagebox.showerror("Error", "Please enter at least one business name")
            return
        
        # Split into list and remove empty lines
        business_list = [name.strip() for name in business_names.split('\n') if name.strip()]
        
        if not business_list:
            messagebox.showerror("Error", "Please enter at least one valid business name")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.current_results = []
        self.progress_var.set(0)
        self.save_btn.config(state=tk.DISABLED)
        
        # Start scraping in a separate thread
        self.is_scraping = True
        threading.Thread(target=self.run_scraper, args=(business_list,), daemon=True).start()
    
    def run_scraper(self, business_list):
        try:
            # Create a temporary file for the scraper
            temp_file = "temp_business_list.txt"
            with open(temp_file, 'w') as f:
                f.write('\n'.join(business_list))
            
            # Initialize scraper
            self.status_var.set("Initializing scraper...")
            scraper = FacebookEmailScraper(temp_file, "temp_results.csv")
            
            # Override the run method to provide progress updates
            original_run = scraper.run
            
            def run_with_progress():
                businesses = scraper.load_business_names()
                total = len(businesses)
                
                for i, business_name in enumerate(businesses):
                    # Update progress
                    progress_pct = (i / total) * 100
                    self.progress_var.set(progress_pct)
                    self.status_var.set(f"Processing: {business_name} ({i+1}/{total})")
                    
                    # Process business
                    if scraper.search_business(business_name):
                        has_website = scraper.check_website_exists()
                        
                        if not has_website:
                            email = scraper.extract_email()
                            
                            if email:
                                result = [business_name, email]
                            else:
                                result = [business_name, "No email found"]
                        else:
                            result = [business_name, "Has website"]
                    else:
                        result = [business_name, "Not accessible"]
                    
                    # Add to results
                    self.current_results.append(result)
                    
                    # Update UI with result
                    self.root.after(0, lambda r=result: self.add_result_to_tree(r))
                    
                    # Small delay between requests
                    time.sleep(2)
                
                # Save results to temp file
                scraper.results = self.current_results
                scraper.save_results()
                
                # Clean up
                scraper.driver.quit()
                
                # Update UI when complete
                self.root.after(0, self.scraping_complete)
            
            # Replace run method
            scraper.run = run_with_progress
            
            # Start scraping
            scraper.setup_driver()
            scraper.run()
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            # Clean up temp files
            if os.path.exists("temp_business_list.txt"):
                try:
                    os.remove("temp_business_list.txt")
                except:
                    pass
    
    def add_result_to_tree(self, result):
        """Add a result to the treeview"""
        self.results_tree.insert("", tk.END, values=result)
    
    def scraping_complete(self):
        """Called when scraping is complete"""
        self.is_scraping = False
        self.progress_var.set(100)
        self.status_var.set(f"Completed! Found {sum(1 for r in self.current_results if r[1] not in ['No email found', 'Has website', 'Not accessible'])} emails")
        self.save_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Complete", "Scraping completed successfully!")
    
    def show_error(self, error_msg):
        """Show error message"""
        self.is_scraping = False
        self.status_var.set("Error occurred")
        messagebox.showerror("Error", f"An error occurred during scraping:\n{error_msg}")
    
    def save_results(self):
        """Save results to CSV file"""
        if not self.current_results:
            messagebox.showinfo("Info", "No results to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Business Name', 'Email'])
                    writer.writerows(self.current_results)
                messagebox.showinfo("Success", f"Results saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {str(e)}")


if __name__ == "__main__":
    # Add missing import
    import time
    
    root = tk.Tk()
    app = FacebookScraperGUI(root)
    root.mainloop() 
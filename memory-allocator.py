import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
from datetime import datetime


# Structure to represent a memory block
class MemoryBlock:
    def __init__(self, start_address, block_size, is_allocated=False, pid=""):
        self.start_address = start_address
        self.size = block_size
        self.allocated = is_allocated
        self.process_id = pid

    def __eq__(self, other):
        if not isinstance(other, MemoryBlock):
            return False
        return (self.start_address == other.start_address and
                self.size == other.size and
                self.allocated == other.allocated and
                self.process_id == other.process_id)


# Memory Allocator class that implements the allocation algorithms
class MemoryAllocator:
    def __init__(self, allocation_algorithm="First-Fit"):
        self.memory = []
        self.total_memory_size = 0
        self.used_memory = 0
        self.algorithm = allocation_algorithm
        self.next_fit_pointer = 0
        self.initialize_memory()

    def initialize_memory(self):
        self.memory = []
        self.total_memory_size = 0
        self.used_memory = 0
        self.next_fit_pointer = 0

        # Initialize with the provided memory blocks
        current_address = 0

        # Add 2KB free block
        self.memory.append(MemoryBlock(current_address, 2, False))
        current_address += 2

        # Add 120KB allocated block
        self.memory.append(MemoryBlock(current_address, 120, True, "Process-A"))
        current_address += 120
        self.used_memory += 120

        # Add 20KB free block
        self.memory.append(MemoryBlock(current_address, 20, False))
        current_address += 20

        # Add 150KB allocated block
        self.memory.append(MemoryBlock(current_address, 150, True, "Process-B"))
        current_address += 150
        self.used_memory += 150

        # Add 160KB allocated block
        self.memory.append(MemoryBlock(current_address, 160, True, "Process-C"))
        current_address += 160
        self.used_memory += 160

        # Add 1KB free block
        self.memory.append(MemoryBlock(current_address, 1, False))
        current_address += 1

        # Add 4KB free block
        self.memory.append(MemoryBlock(current_address, 4, False))
        current_address += 4

        # Add 554KB allocated block
        self.memory.append(MemoryBlock(current_address, 554, True, "Process-D"))
        current_address += 554
        self.used_memory += 554

        # Add 124KB free block
        self.memory.append(MemoryBlock(current_address, 124, False))
        current_address += 124

        self.total_memory_size = current_address

    def set_algorithm(self, allocation_algorithm):
        self.algorithm = allocation_algorithm
        self.next_fit_pointer = 0  # Reset Next-Fit pointer

    def get_memory_blocks(self):
        return self.memory

    def get_memory_stats(self):
        total = self.total_memory_size
        used = self.used_memory
        free = self.total_memory_size - self.used_memory
        fragmentation = self.calculate_fragmentation()
        return total, used, free, fragmentation

    def allocate_memory(self, size, process_id):
        if self.algorithm == "First-Fit":
            return self.first_fit(size, process_id)
        elif self.algorithm == "Best-Fit":
            return self.best_fit(size, process_id)
        elif self.algorithm == "Worst-Fit":
            return self.worst_fit(size, process_id)
        elif self.algorithm == "Next-Fit":
            return self.next_fit(size, process_id)
        return False

    def first_fit(self, size, process_id):
        for i, block in enumerate(self.memory):
            if not block.allocated and block.size >= size:
                self.allocate_block(i, size, process_id)
                return True
        return False  # No suitable block found

    def best_fit(self, size, process_id):
        best_block_idx = -1
        min_extra_space = self.total_memory_size + 1

        for i, block in enumerate(self.memory):
            if not block.allocated and block.size >= size:
                extra_space = block.size - size
                if extra_space < min_extra_space:
                    min_extra_space = extra_space
                    best_block_idx = i

        if best_block_idx != -1:
            self.allocate_block(best_block_idx, size, process_id)
            return True
        return False  # No suitable block found

    def worst_fit(self, size, process_id):
        worst_block_idx = -1
        max_extra_space = -1

        for i, block in enumerate(self.memory):
            if not block.allocated and block.size >= size:
                extra_space = block.size - size
                if extra_space > max_extra_space:
                    max_extra_space = extra_space
                    worst_block_idx = i

        if worst_block_idx != -1:
            self.allocate_block(worst_block_idx, size, process_id)
            return True
        return False  # No suitable block found

    def next_fit(self, size, process_id):
        if not self.memory:
            return False

        # Start from next_fit_pointer and wrap around when end is reached
        start_idx = self.next_fit_pointer
        current_idx = start_idx

        while True:
            if not self.memory[current_idx].allocated and self.memory[current_idx].size >= size:
                self.allocate_block(current_idx, size, process_id)
                self.next_fit_pointer = (current_idx + 1) % len(self.memory)
                return True
            current_idx = (current_idx + 1) % len(self.memory)
            if current_idx == start_idx:
                break

        return False  # No suitable block found

    def process_exists(self, process_id):
        """
        Check if a process with the given ID already exists in memory
        """
        for block in self.memory:
            if block.allocated and block.process_id == process_id:
                return True
        return False

    def allocate_memory(self, size, process_id):
        # First check if the process ID already exists
        if self.process_exists(process_id):
            return False, "duplicate_process"

        # Proceed with allocation based on the algorithm
        if self.algorithm == "First-Fit":
            success = self.first_fit(size, process_id)
        elif self.algorithm == "Best-Fit":
            success = self.best_fit(size, process_id)
        elif self.algorithm == "Worst-Fit":
            success = self.worst_fit(size, process_id)
        elif self.algorithm == "Next-Fit":
            success = self.next_fit(size, process_id)
        else:
            success = False

        if success:
            return True, "success"
        else:
            return False, "no_memory"  # No suitable block found

    def allocate_block(self, block_idx, size, process_id):
        block = self.memory[block_idx]
        if block.size == size:
            # If the block is exactly the size we need
            block.allocated = True
            block.process_id = process_id
        else:
            # If the block is larger, split it
            remaining_size = block.size - size
            block.size = size
            block.allocated = True
            block.process_id = process_id

            # Create a new block for the remaining space
            self.memory.insert(block_idx + 1, MemoryBlock(block.start_address + size, remaining_size, False))

        self.used_memory += size

    def deallocate_memory(self, process_id):
        found = False
        for block in self.memory:
            if block.allocated and block.process_id == process_id:
                block.allocated = False
                block.process_id = ""
                self.used_memory -= block.size
                found = True

        if found:
            self.merge_adjacent_free_blocks()
            return True
        return False

    def merge_adjacent_free_blocks(self):
        i = 0
        while i < len(self.memory) - 1:
            if not self.memory[i].allocated and not self.memory[i + 1].allocated:
                # Merge the blocks
                self.memory[i].size += self.memory[i + 1].size
                self.memory.pop(i + 1)
            else:
                i += 1

    def calculate_fragmentation(self):
        total_free_memory = self.total_memory_size - self.used_memory
        largest_free_block = 0

        for block in self.memory:
            if not block.allocated and block.size > largest_free_block:
                largest_free_block = block.size

        # If there's no free memory, there's no fragmentation
        if total_free_memory == 0:
            return 0.0

        # External fragmentation is the percentage of free memory that cannot be allocated
        # to satisfy the largest possible request (which would be the size of the largest free block)
        fragmentation = ((total_free_memory - largest_free_block) / total_free_memory) * 100
        return fragmentation

    def reset_memory(self):
        self.initialize_memory()


# Custom memory visualization panel using Tkinter Canvas
class MemoryVisualPanel(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.memory_blocks = []
        self.configure(bg="white", height=100)  # Default height for the memory visualization

    def update_memory_blocks(self, blocks):
        self.memory_blocks = blocks
        self.redraw()

    def redraw(self):
        self.delete("all")  # Clear the canvas

        # Calculate total memory size for scaling
        total_size = sum(block.size for block in self.memory_blocks)

        # Get canvas dimensions
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1:  # Canvas not yet drawn
            return

        # Draw memory blocks
        x = 0
        for block in self.memory_blocks:
            # Calculate block width proportionally
            block_width = max(1, int((block.size / total_size) * width))

            # Set color based on allocation status
            if block.allocated:
                # Generate a color based on the process ID for consistent coloring
                hash_val = 0
                for c in block.process_id:
                    hash_val = hash_val * 31 + ord(c)
                r = (hash_val & 0xFF) % 200 + 55  # Keep colors not too dark or light
                g = ((hash_val >> 8) & 0xFF) % 200 + 55
                b = ((hash_val >> 16) & 0xFF) % 200 + 55
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#dcdcdc"  # Light gray for free blocks

            # Draw the block
            self.create_rectangle(x, 0, x + block_width, height, fill=color, outline="black")

            # Draw size and process ID text
            if block.allocated:
                label = f"{block.size}KB\n{block.process_id}"
            else:
                label = f"{block.size}KB\nFree"

            # Try to fit text in the block
            if block_width > 40:  # Only if there's enough space
                self.create_text(x + block_width // 2, height // 2, text=label, anchor="center")

            x += block_width


# Main application frame
class MemoryAllocatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Allocation Simulator")
        self.root.geometry("900x700")

        self.allocator = MemoryAllocator()

        # Configure the grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(6, weight=1)  # For the memory grid
        self.root.grid_rowconfigure(7, weight=1)  # For the log text area

        # Create main frames
        self.create_control_frame()
        self.create_visualization_frame()
        self.create_allocation_frame()
        self.create_deallocation_frame()
        self.create_stats_frame()
        self.create_memory_grid()
        self.create_log_text()

        # Initialize the display
        self.update_display()
        self.log_message("Memory Allocation Simulator started with First-Fit algorithm.")
        self.log_message("Initial memory blocks loaded.")

        # Schedule a redraw for the visualization panel after the window appears
        self.root.after(100, self.visual_panel.redraw)

    def create_control_frame(self):
        control_frame = ttk.LabelFrame(self.root, text="Control Panel")
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Algorithm selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=0, padx=5, pady=5)

        self.algorithm_var = tk.StringVar(value="First-Fit")
        algorithm_combo = ttk.Combobox(control_frame, textvariable=self.algorithm_var,
                                       values=["First-Fit", "Best-Fit", "Worst-Fit", "Next-Fit"])
        algorithm_combo.grid(row=0, column=1, padx=5, pady=5)
        algorithm_combo.bind("<<ComboboxSelected>>", self.on_algorithm_change)

        # Reset button
        reset_button = ttk.Button(control_frame, text="Reset Memory", command=self.on_reset_memory)
        reset_button.grid(row=0, column=2, padx=5, pady=5)

    def create_visualization_frame(self):
        visual_frame = ttk.LabelFrame(self.root, text="Memory Visualization")
        visual_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        visual_frame.grid_columnconfigure(0, weight=1)

        self.visual_panel = MemoryVisualPanel(visual_frame, bg="white", height=100)
        self.visual_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    def create_allocation_frame(self):
        allocation_frame = ttk.LabelFrame(self.root, text="Memory Allocation")
        allocation_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(allocation_frame, text="Size (KB):").grid(row=0, column=0, padx=5, pady=5)
        self.process_size_entry = ttk.Entry(allocation_frame, width=10)
        self.process_size_entry.insert(0, "10")
        self.process_size_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(allocation_frame, text="Process ID:").grid(row=0, column=2, padx=5, pady=5)
        self.process_id_entry = ttk.Entry(allocation_frame, width=15)
        self.process_id_entry.insert(0, "Process-E")
        self.process_id_entry.grid(row=0, column=3, padx=5, pady=5)

        allocate_button = ttk.Button(allocation_frame, text="Allocate Memory", command=self.on_allocate_memory)
        allocate_button.grid(row=0, column=4, padx=5, pady=5)

    def create_deallocation_frame(self):
        deallocation_frame = ttk.LabelFrame(self.root, text="Memory Deallocation")
        deallocation_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(deallocation_frame, text="Process ID:").grid(row=0, column=0, padx=5, pady=5)
        self.deallocate_id_entry = ttk.Entry(deallocation_frame, width=15)
        self.deallocate_id_entry.insert(0, "Process-A")
        self.deallocate_id_entry.grid(row=0, column=1, padx=5, pady=5)

        deallocate_button = ttk.Button(deallocation_frame, text="Deallocate Memory", command=self.on_deallocate_memory)
        deallocate_button.grid(row=0, column=2, padx=5, pady=5)

    def create_stats_frame(self):
        stats_frame = ttk.LabelFrame(self.root, text="Memory Statistics")
        stats_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)

        self.total_memory_label = ttk.Label(stats_frame, text="Total Memory: 0 KB")
        self.total_memory_label.grid(row=0, column=0, padx=5, pady=5)

        self.used_memory_label = ttk.Label(stats_frame, text="Used: 0 KB (0%)")
        self.used_memory_label.grid(row=0, column=1, padx=5, pady=5)

        self.free_memory_label = ttk.Label(stats_frame, text="Free: 0 KB (0%)")
        self.free_memory_label.grid(row=0, column=2, padx=5, pady=5)

        self.fragmentation_label = ttk.Label(stats_frame, text="Fragmentation: 0%")
        self.fragmentation_label.grid(row=0, column=3, padx=5, pady=5)

    def create_memory_grid(self):
        grid_frame = ttk.LabelFrame(self.root, text="Memory Blocks")
        grid_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview for memory blocks
        columns = ('address', 'size', 'status', 'process_id')
        self.memory_tree = ttk.Treeview(grid_frame, columns=columns, show='headings')

        # Define headings
        self.memory_tree.heading('address', text='Address')
        self.memory_tree.heading('size', text='Size (KB)')
        self.memory_tree.heading('status', text='Status')
        self.memory_tree.heading('process_id', text='Process ID')

        # Define column widths
        self.memory_tree.column('address', width=100)
        self.memory_tree.column('size', width=100)
        self.memory_tree.column('status', width=100)
        self.memory_tree.column('process_id', width=150)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, command=self.memory_tree.yview)
        self.memory_tree.configure(yscroll=scrollbar.set)

        # Grid layout for treeview and scrollbar
        self.memory_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

    def create_log_text(self):
        log_frame = ttk.LabelFrame(self.root, text="Event Log")
        log_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)  # Make read-only

    def update_display(self):
        # Update memory visualization
        self.visual_panel.update_memory_blocks(self.allocator.get_memory_blocks())

        # Update memory tree
        # Clear existing items
        for item in self.memory_tree.get_children():
            self.memory_tree.delete(item)

        # Add memory blocks
        blocks = self.allocator.get_memory_blocks()
        for block in blocks:
            status = "Allocated" if block.allocated else "Free"
            process_id = block.process_id if block.allocated else "-"

            item_id = self.memory_tree.insert('', 'end', values=(
                block.start_address,
                block.size,
                status,
                process_id
            ))

            # Color the row based on allocation status
            if block.allocated:
                self.memory_tree.item(item_id, tags=('allocated',))
            else:
                self.memory_tree.item(item_id, tags=('free',))

        # Configure tags for coloring
        self.memory_tree.tag_configure('allocated', background='#ffcccc')  # Light red
        self.memory_tree.tag_configure('free', background='#ccffcc')  # Light green

        # Update memory stats
        total, used, free, fragmentation = self.allocator.get_memory_stats()

        self.total_memory_label.config(text=f"Total Memory: {total} KB")
        self.used_memory_label.config(text=f"Used: {used} KB ({used / total * 100:.2f}%)")
        self.free_memory_label.config(text=f"Free: {free} KB ({free / total * 100:.2f}%)")
        self.fragmentation_label.config(text=f"Fragmentation: {fragmentation:.2f}%")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.config(state=tk.DISABLED)

    def on_algorithm_change(self, event):
        algorithm = self.algorithm_var.get()
        self.allocator.set_algorithm(algorithm)
        self.log_message(f"Switched to {algorithm} algorithm.")

    def on_reset_memory(self):
        self.allocator.reset_memory()
        self.update_display()
        self.log_message("Memory reset to initial state.")

    def on_allocate_memory(self):
        try:
            size = int(self.process_size_entry.get())
            if size <= 0:
                messagebox.showerror("Invalid Input", "Please enter a valid size (positive integer).")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid size (positive integer).")
            return

        process_id = self.process_id_entry.get()
        if not process_id:
            messagebox.showerror("Invalid Input", "Please enter a process ID.")
            return

        success, reason = self.allocator.allocate_memory(size, process_id)

        if success:
            self.log_message(f"Allocated {size} KB for {process_id} successfully.")
        else:
            if reason == "duplicate_process":
                self.log_message(f"Failed to allocate {size} KB for {process_id}. Process ID already exists.")
                messagebox.showerror("Allocation Failed",
                                     f"Process ID '{process_id}' already exists. Please use a unique process ID.")
            else:  # no_memory
                self.log_message(f"Failed to allocate {size} KB for {process_id}. Not enough memory.")
                messagebox.showinfo("Allocation Failed", "Allocation failed. Not enough continuous memory available.")

        self.update_display()

    def on_deallocate_memory(self):
        process_id = self.deallocate_id_entry.get()
        if not process_id:
            messagebox.showerror("Invalid Input", "Please enter a process ID to deallocate.")
            return

        success = self.allocator.deallocate_memory(process_id)
        if success:
            self.log_message(f"Deallocated memory for {process_id} successfully.")
        else:
            self.log_message(f"Failed to deallocate memory for {process_id}. Process not found.")
            messagebox.showinfo("Deallocation Failed", "Deallocation failed. Process ID not found.")

        self.update_display()


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryAllocatorApp(root)
    root.mainloop()

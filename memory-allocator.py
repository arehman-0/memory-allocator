import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# Structure to represent a memory block
class MemoryBlock:
    def __init__(self, start_address: int, block_size: int, is_allocated=False, pid=""):
        self.start_address = start_address
        self.size = block_size
        self.allocated = is_allocated
        self.process_id = pid

    def __eq__(self, other):
        if not isinstance(other, MemoryBlock):
            return False
        return (
            self.start_address == other.start_address
            and self.size == other.size
            and self.allocated == other.allocated
            and self.process_id == other.process_id
        )

    def __str__(self):
        status = f"Allocated ({self.process_id})" if self.allocated else "Free"
        return f"Block(Addr={self.start_address}, Size={self.size}KB, Status={status})"


class MemoryAllocator:
    memory: list[MemoryBlock]
    total_memory_size: int
    used_memory: int

    def __init__(self):
        self.memory = []
        self.total_memory_size = 0
        self.used_memory = 0
        self.initialize_memory()

    def initialize_memory(self):
        """Resets memory to its initial predefined state."""
        self.memory = []
        self.total_memory_size = 0
        self.used_memory = 0
        current_address = 0

        initial_layout = [
            (2, False, ""),
            (120, True, "Process-A"),
            (20, False, ""),
            (150, True, "Process-B"),
            (160, True, "Process-C"),
            (1, False, ""),
            (4, False, ""),
            (554, True, "Process-D"),
            (124, False, ""),
        ]

        for size, allocated, pid in initial_layout:
            self.memory.append(MemoryBlock(current_address, size, allocated, pid))
            if allocated:
                self.used_memory += size
            current_address += size

        self.total_memory_size = current_address
        print(
            f"Memory Initialized: Total={self.total_memory_size}, Used={self.used_memory}"
        )

    def get_memory_blocks(self) -> list[MemoryBlock]:
        """Returns the current list of memory blocks."""
        return self.memory

    def get_memory_stats(self) -> tuple[int, int, int, float]:
        """Returns total size, used size, free size, and fragmentation %."""
        total = self.total_memory_size
        used = self.used_memory
        free = total - used
        fragmentation = self.calculate_fragmentation()
        return total, used, free, fragmentation

    def allocate_memory(self, size: int, process_id: str) -> tuple[bool, str]:
        """
        Allocates memory using the First-Fit algorithm.
        Returns (success_status, message_code).
        message_code can be 'success', 'duplicate_process', 'allocation_error'.
        """
        if size <= 0:
            return False, "invalid_size"

        if self.process_exists(process_id):
            return False, "duplicate_process"

        allocated = False
        for i, block in enumerate(self.memory):
            if not block.allocated and block.size >= size:
                self.allocate_block(i, size, process_id)
                allocated = True
                break

        if allocated:
            return True, "success"
        else:
            return False, "allocation_error"

    def process_exists(self, process_id: str) -> bool:
        """Checks if a process ID is already allocated in memory."""
        for block in self.memory:
            if block.allocated and block.process_id == process_id:
                return True
        return False

    def allocate_block(self, block_idx: int, size: int, process_id: str):
        """Internal helper to allocate within a specific block, splitting if necessary."""
        block = self.memory[block_idx]
        original_block_size = block.size

        if block.size == size:
            # If the block is exactly the size we need
            block.allocated = True
            block.process_id = process_id
            print(f"Allocated exact block {block_idx} ({size}KB) to {process_id}")
        elif block.size > size:
            # If the block is larger, split it
            remaining_size = block.size - size
            block.size = size
            block.allocated = True
            block.process_id = process_id

            # Create a new block for the remaining space
            new_free_block = MemoryBlock(
                block.start_address + size, remaining_size, False, ""
            )
            self.memory.insert(block_idx + 1, new_free_block)
            print(
                f"Split block {block_idx} ({original_block_size}KB): allocated {size}KB to {process_id}, remaining {remaining_size}KB free."
            )
        else:
            print(
                f"Error: Tried to allocate {size}KB in block {block_idx} with size {block.size}KB"
            )
            return

        self.used_memory += size

    def deallocate_memory(self, process_id: str) -> bool:
        """Deallocates all memory blocks assigned to a specific process ID."""
        found = False
        deallocated_size = 0
        indices_to_check_merge = set()

        # Iterate backwards to handle potential merging correctly after removals if needed
        # (Although we don't remove, just mark free, iterating forward is fine here)
        for i, block in enumerate(self.memory):
            if block.allocated and block.process_id == process_id:
                print(f"Deallocating block {i} (Size: {block.size}KB) for {process_id}")
                deallocated_size += block.size
                block.allocated = False
                block.process_id = ""
                found = True
                # Record indices near the freed block for potential merging
                if i > 0:
                    indices_to_check_merge.add(i - 1)
                indices_to_check_merge.add(
                    i
                )  # Check the freed block itself with its right neighbor

        if found:
            self.used_memory -= deallocated_size
            print(
                f"Total deallocated: {deallocated_size}KB. Used memory now: {self.used_memory}"
            )
            self.merge_adjacent_free_blocks(
                indices_to_check_merge
            )  # Pass relevant indices
            return True

        return False

    def merge_adjacent_free_blocks(
        self, indices_to_start_check: set[int] | None = None
    ):
        """Merges adjacent free blocks. Can be optimized to check only around recent changes."""
        merged = False
        i = 0
        while i < len(self.memory) - 1:
            # Only perform merge check if blocks at i and i+1 are free
            if not self.memory[i].allocated and not self.memory[i + 1].allocated:
                print(
                    f"Merging free blocks at index {i} ({self.memory[i].size}KB) and {i+1} ({self.memory[i+1].size}KB)"
                )
                # Merge block i+1 into block i
                self.memory[i].size += self.memory[i + 1].size
                # Remove block i+1
                self.memory.pop(i + 1)
                merged = True
                # Don't increment i, as the new block at i might need merging with the next one
                continue  # Re-evaluate the current index i
            i += 1

        if merged:
            print("Finished merging adjacent free blocks.")
            # for block in self.memory: print(f"  {block}") # Optional: print state after merge

    def calculate_fragmentation(self) -> float:
        """Calculates external fragmentation percentage."""
        total_free_memory = self.total_memory_size - self.used_memory
        largest_free_block = 0

        for block in self.memory:
            if not block.allocated:
                if block.size > largest_free_block:
                    largest_free_block = block.size

        # If there's no free memory, or only one free block (which is the largest)
        if total_free_memory == 0:
            return 0.0

        # External fragmentation: % of free memory not in the largest block
        unusable_free_space = total_free_memory - largest_free_block
        if unusable_free_space < 0:
            unusable_free_space = 0  # Sanity check

        fragmentation = (unusable_free_space / total_free_memory) * 100
        return fragmentation

    def reset_memory(self):
        """Resets the memory to the initial state."""
        self.initialize_memory()


class MemoryVisualPanel(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.memory_blocks = []
        self.configure(bg="white", height=100, bd=1, relief="sunken")
        self.bind("<Configure>", self.on_resize)

    def update_memory_blocks(self, blocks: list[MemoryBlock]):
        """Stores the latest memory blocks and triggers a redraw."""
        self.memory_blocks = blocks
        self.redraw()

    def on_resize(self, event=None):
        """Callback function when the canvas is resized."""
        self.redraw()

    def redraw(self):
        """Clears and redraws the memory blocks on the canvas."""
        self.delete("all")

        if not self.memory_blocks:
            return

        # Calculate total memory size for scaling
        total_size = sum(block.size for block in self.memory_blocks)
        if total_size == 0:  # Avoid division by zero if memory is empty
            return

        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet properly sized
            return

        # Draw memory blocks
        current_x = 0
        for block in self.memory_blocks:
            block_width = max(2, (block.size / total_size) * canvas_width)

            end_x = current_x + block_width

            if block.allocated:
                color = "#7d9b68"
            else:
                color = "#dcdcdc"

            # Draw the rectangle
            self.create_rectangle(
                current_x, 0, end_x, canvas_height, fill=color, outline="black", width=1
            )

            # --- Draw Text ---
            if block.allocated:
                text_label = f"{block.size}K\n{block.process_id}"
            else:
                text_label = f"{block.size}K\n(Free)"

            # Only draw text if the block is wide enough
            # Estimate text width roughly (very approximate)
            font_size = 8
            estimated_text_width = max(
                len(str(block.size)) + 1,
                len(block.process_id if block.allocated else "(Free)"),
            ) * (font_size * 0.6)

            if block_width > estimated_text_width + 4 and canvas_height > 20:
                text_x = current_x + block_width / 2
                text_y = canvas_height / 2
                self.create_text(
                    text_x,
                    text_y,
                    text=text_label,
                    anchor="center",
                    font=("Helvetica", font_size),
                )  # Smaller font

            current_x = end_x

        # Ensure the last block reaches the edge if rounding caused gaps
        if current_x < canvas_width:
            self.create_rectangle(
                current_x,
                0,
                canvas_width,
                canvas_height,
                fill="#EEEEEE",
                outline="black",
            )  # Fill gap


class MemoryAllocatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Memory Allocation Simulator - First-Fit")
        self.root.geometry("900x750")

        self.allocator = MemoryAllocator()

        # Configure the grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(5, weight=1)  # Make memory grid row expandable
        self.root.grid_rowconfigure(6, weight=1)  # Make log text area row expandable

        self.create_menubar()
        self.create_heading()
        self.create_visualization_frame()
        self.create_allocation_frame()
        self.create_deallocation_frame()
        self.create_stats_frame()
        self.create_memory_grid()
        self.create_log_text()

        # Initialize the display
        self.update_display()
        self.log_message(
            "Memory Allocation Simulator started with First-Fit algorithm."
        )
        self.log_message(
            f"Initial memory loaded. Total: {self.allocator.total_memory_size}KB"
        )

        self.root.after(100, self.visual_panel.redraw)

    def create_menubar(self):
        menubar = tk.Menu(self.root)

        menubar.add_command(label="Info", command=self.show_info)
        menubar.add_command(label="About", command=self.show_about)

        self.root.config(menu=menubar)

    def create_heading(self):
        heading_label = ttk.Label(
            self.root,
            text="Memory Allocation Simulator - First-Fit Algorithm",
            padding=10,
            font=("Helvetica", 14, "bold"),
            anchor="center",
        )
        heading_label.grid(row=0, column=0, pady=(10, 15), sticky="ew")

    def create_visualization_frame(self):
        visual_frame = ttk.LabelFrame(self.root, text="Memory Visualization")
        visual_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        visual_frame.grid_columnconfigure(0, weight=1)

        self.visual_panel = MemoryVisualPanel(visual_frame)
        self.visual_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    def create_allocation_frame(self):
        allocation_frame = ttk.LabelFrame(self.root, text="Memory Allocation")
        allocation_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(allocation_frame, text="Size (KB):").grid(
            row=0, column=0, padx=(5, 2), pady=5, sticky="w"
        )
        self.process_size_entry = ttk.Entry(allocation_frame, width=10)
        self.process_size_entry.insert(0, "10")
        self.process_size_entry.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")

        ttk.Label(allocation_frame, text="Process ID:").grid(
            row=0, column=2, padx=(10, 2), pady=5, sticky="w"
        )
        self.process_id_entry = ttk.Entry(allocation_frame, width=15)
        self.process_id_entry.insert(0, "Process-E")
        self.process_id_entry.grid(row=0, column=3, padx=(0, 5), pady=5, sticky="w")

        allocate_button = ttk.Button(
            allocation_frame, text="Allocate Memory", command=self.on_allocate_memory
        )
        allocate_button.grid(row=0, column=4, padx=(10, 5), pady=5, sticky="w")

    def create_deallocation_frame(self):
        deallocation_frame = ttk.LabelFrame(
            self.root, text="Memory Deallocation / Reset"
        )
        deallocation_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        deallocation_frame.grid_columnconfigure(0, weight=0)  # Label
        deallocation_frame.grid_columnconfigure(1, weight=0)  # Entry
        deallocation_frame.grid_columnconfigure(2, weight=0)  # Dealloc Button
        deallocation_frame.grid_columnconfigure(
            3, weight=1
        )  # Expanding Spacer Column <<<<
        deallocation_frame.grid_columnconfigure(4, weight=0)  # Reset Button

        # Left-aligned elements
        ttk.Label(deallocation_frame, text="Process ID:").grid(
            row=0, column=0, padx=(5, 2), pady=5, sticky="w"
        )
        self.deallocate_id_entry = ttk.Entry(deallocation_frame, width=15)
        self.deallocate_id_entry.insert(0, "Process-A")
        self.deallocate_id_entry.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")

        deallocate_button = ttk.Button(
            deallocation_frame,
            text="Deallocate Memory",
            command=self.on_deallocate_memory,
        )
        deallocate_button.grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

        # --- New Reset Button ---
        # Placed in column 4, after the expanding column 3
        reset_button = ttk.Button(
            deallocation_frame, text="Reset Memory", command=self.on_reset_memory
        )
        reset_button.grid(row=0, column=4, padx=5, pady=5, sticky="e")

    def create_stats_frame(self):
        stats_frame = ttk.LabelFrame(self.root, text="Memory Statistics")
        stats_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)

        self.total_memory_label = ttk.Label(stats_frame, text="Total: 0 KB", anchor="w")
        self.total_memory_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.used_memory_label = ttk.Label(
            stats_frame, text="Used: 0 KB (0.00%)", anchor="w"
        )
        self.used_memory_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.free_memory_label = ttk.Label(
            stats_frame, text="Free: 0 KB (0.00%)", anchor="w"
        )
        self.free_memory_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.fragmentation_label = ttk.Label(
            stats_frame, text="Frag: 0.00%", anchor="w"
        )
        self.fragmentation_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    def create_memory_grid(self):
        grid_frame = ttk.LabelFrame(self.root, text="Memory Blocks Details")
        grid_frame.grid(
            row=5, column=0, sticky="nsew", padx=10, pady=5
        )  # nsew allows vertical expansion
        grid_frame.grid_columnconfigure(0, weight=1)  # Treeview expands horizontally
        grid_frame.grid_rowconfigure(0, weight=1)  # Treeview expands vertically

        columns = ("address", "size", "status", "process_id")
        self.memory_tree = ttk.Treeview(
            grid_frame, columns=columns, show="headings", height=7
        )

        # Define headings
        self.memory_tree.heading("address", text="Start Addr", anchor="w")
        self.memory_tree.heading("size", text="Size (KB)", anchor="e")
        self.memory_tree.heading("status", text="Status", anchor="w")
        self.memory_tree.heading("process_id", text="Process ID", anchor="w")

        # Define column widths and alignment
        self.memory_tree.column("address", width=100, stretch=tk.NO, anchor="e")
        self.memory_tree.column("size", width=100, stretch=tk.NO, anchor="e")
        self.memory_tree.column("status", width=100, stretch=tk.NO, anchor="w")
        self.memory_tree.column("process_id", width=150, stretch=tk.YES, anchor="w")

        # Create scrollbar
        scrollbar = ttk.Scrollbar(
            grid_frame, orient=tk.VERTICAL, command=self.memory_tree.yview
        )
        self.memory_tree.configure(yscroll=scrollbar.set)

        # Grid layout for treeview and scrollbar
        self.memory_tree.grid(row=0, column=0, sticky="nsew")  # nsew allows expansion
        scrollbar.grid(row=0, column=1, sticky="ns")  # Only vertical sticky needed

    def create_log_text(self):
        log_frame = ttk.LabelFrame(self.root, text="Event Log")
        log_frame.grid(
            row=6, column=0, sticky="nsew", padx=10, pady=5
        )  # nsew allows vertical expansion
        log_frame.grid_columnconfigure(0, weight=1)  # Text widget expands horizontally
        log_frame.grid_rowconfigure(0, weight=1)  # Text widget expands vertically

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=8, state=tk.DISABLED
        )  # Start disabled
        self.log_text.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )  # nsew allows expansion

    def update_display(self):
        """Refreshes all parts of the GUI based on the current allocator state."""
        blocks = self.allocator.get_memory_blocks()

        # Update memory visualization
        self.visual_panel.update_memory_blocks(blocks)

        # Update memory tree
        # Clear existing items
        for item in self.memory_tree.get_children():
            self.memory_tree.delete(item)

        # Add memory blocks
        for i, block in enumerate(blocks):
            status = "Allocated" if block.allocated else "Free"
            process_id = block.process_id if block.allocated else "---"

            item_id = self.memory_tree.insert(
                "",
                "end",
                iid=f"block_{i}",
                values=(
                    f"{block.start_address:06X}",  # Display address in Hex
                    f"{block.size}",
                    status,
                    process_id,
                ),
            )

            # Color the row based on allocation status using tags
            tag = "allocated" if block.allocated else "free"
            self.memory_tree.item(item_id, tags=(tag,))

        # Configure tags for coloring (do this once or ensure it's reapplied if needed)
        self.memory_tree.tag_configure("allocated", background="#FFD2D2")  # Lighter red
        self.memory_tree.tag_configure("free", background="#D2FFD2")  # Lighter green

        # Update memory stats
        total, used, free, fragmentation = self.allocator.get_memory_stats()
        used_percent = (used / total * 100) if total > 0 else 0
        free_percent = (free / total * 100) if total > 0 else 0

        self.total_memory_label.config(text=f"Total: {total} KB")
        self.used_memory_label.config(text=f"Used: {used} KB ({used_percent:.2f}%)")
        self.free_memory_label.config(text=f"Free: {free} KB ({free_percent:.2f}%)")
        self.fragmentation_label.config(text=f"Frag: {fragmentation:.2f}%")

    def log_message(self, message: str):
        """Adds a timestamped message to the log area."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        self.log_text.config(state=tk.NORMAL)  # Enable writing
        self.log_text.insert(tk.END, f"{timestamp} - {message}\n")
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.config(state=tk.DISABLED)  # Disable writing

    def on_reset_memory(self):
        """Handles the Reset Memory button click."""
        if messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset the memory to its initial state?",
        ):
            self.log_message("Resetting memory...")
            self.allocator.reset_memory()
            self.update_display()
            self.log_message("Memory reset to initial state.")

    def on_allocate_memory(self):
        """Handles the Allocate Memory button click."""
        try:
            size_str = self.process_size_entry.get()
            size = int(size_str)
            if size <= 0:
                messagebox.showerror(
                    "Invalid Input", "Please enter a positive size (KB)."
                )
                self.log_message(
                    f"Allocation attempt failed: Invalid size '{size_str}'."
                )
                return
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please enter a valid integer size (KB)."
            )
            self.log_message(
                f"Allocation attempt failed: Non-integer size '{self.process_size_entry.get()}'."
            )
            return

        process_id = (
            self.process_id_entry.get().strip()
        )  # Remove leading/trailing whitespace
        if not process_id:
            messagebox.showerror(
                "Invalid Input", "Please enter a non-empty Process ID."
            )
            self.log_message("Allocation attempt failed: Empty Process ID.")
            return

        self.log_message(f"Attempting to allocate {size} KB for '{process_id}'...")
        success, reason = self.allocator.allocate_memory(size, process_id)

        if success:
            self.log_message(f"SUCCESS: Allocated {size} KB for '{process_id}'.")
        else:
            error_msg = f"FAILED to allocate {size} KB for '{process_id}'."
            if reason == "duplicate_process":
                error_msg += " Reason: Process ID already exists."
                messagebox.showerror(
                    "Allocation Failed",
                    f"Process ID '{process_id}' already exists. Please use a unique ID.",
                )
            elif reason == "allocation_error":
                error_msg += " Reason: No single free block large enough (First-Fit)."
                messagebox.showinfo(
                    "Allocation Failed",
                    f"Could not find a suitable free block of size {size} KB or larger.",
                )
            else:
                error_msg += f" Reason: Unknown ({reason})."
                messagebox.showerror(
                    "Allocation Error", f"An unexpected error occurred ({reason})."
                )
            self.log_message(error_msg)

        self.update_display()

    def on_deallocate_memory(self):
        """Handles the Deallocate Memory button click."""
        process_id = self.deallocate_id_entry.get().strip()
        if not process_id:
            messagebox.showerror(
                "Invalid Input", "Please enter a Process ID to deallocate."
            )
            self.log_message("Deallocation attempt failed: Empty Process ID.")
            return

        self.log_message(f"Attempting to deallocate memory for '{process_id}'...")
        success = self.allocator.deallocate_memory(process_id)

        if success:
            self.log_message(
                f"SUCCESS: Deallocated memory for '{process_id}'. Merged adjacent free blocks if possible."
            )
        else:
            self.log_message(
                f"FAILED to deallocate memory for '{process_id}'. Reason: Process ID not found."
            )
            messagebox.showinfo(
                "Deallocation Failed",
                f"Process ID '{process_id}' not found in allocated memory.",
            )

        self.update_display()

    def show_info(e=None):
        # Create a new window
        info_window = tk.Toplevel()
        info_window.title("Memory Allocation Algorithms")
        info_window.geometry("900x600")
        info_window.minsize(600, 400)

        # Create styles
        style = ttk.Style()
        style.configure(
            "Title.TLabel", font=("Arial", 16, "bold"), foreground="#003366", padding=10
        )
        style.configure(
            "Heading.TLabel",
            font=("Arial", 14, "bold"),
            foreground="#004080",
            padding=(5, 10, 5, 5),
        )
        style.configure(
            "Subheading.TLabel",
            font=("Arial", 12, "bold"),
            foreground="#0066CC",
            padding=(5, 8, 5, 3),
        )
        style.configure("Normal.TLabel", font=("Arial", 11), padding=(5, 2))

        # Main frame with scrollbar
        main_frame = ttk.Frame(info_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas with scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a frame inside the canvas
        content_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # Title
        title_label = ttk.Label(
            content_frame, text="Memory Allocation Algorithms", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Introduction
        intro_text = (
            "Memory allocation is a fundamental process in operating systems and programming languages where "
            "processes or programs are assigned space in memory. Efficient memory allocation is crucial for "
            "system performance and stability. Various algorithms exist to manage this task, each with its "
            "own advantages and disadvantages."
        )
        intro_label = ttk.Label(
            content_frame, text=intro_text, style="Normal.TLabel", wraplength=750
        )
        intro_label.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Heading for algorithms section
        algorithms_heading = ttk.Label(
            content_frame,
            text="Common Memory Allocation Algorithms",
            style="Heading.TLabel",
        )
        algorithms_heading.grid(row=2, column=0, sticky="w")

        # 1. First Fit
        first_fit_heading = ttk.Label(
            content_frame, text="1. First Fit", style="Subheading.TLabel"
        )
        first_fit_heading.grid(row=3, column=0, sticky="w")

        first_fit_frame = ttk.Frame(content_frame)
        first_fit_frame.grid(row=4, column=0, sticky="w", padx=20)

        first_fit_process = ttk.Label(
            first_fit_frame, text="Process:", font=("Arial", 11, "bold")
        )
        first_fit_process.grid(row=0, column=0, sticky="w")
        first_fit_process_text = ttk.Label(
            first_fit_frame,
            text="Start searching from the beginning of the memory.",
            style="Normal.TLabel",
        )
        first_fit_process_text.grid(row=0, column=1, sticky="w", padx=(5, 0))

        first_fit_action = ttk.Label(
            first_fit_frame, text="Action:", font=("Arial", 11, "bold")
        )
        first_fit_action.grid(row=1, column=0, sticky="w")
        first_fit_action_text = ttk.Label(
            first_fit_frame,
            text="Allocate the requested memory from the first free block encountered that is \n"
            "equal to or larger than the requested size.",
            style="Normal.TLabel",
        )
        first_fit_action_text.grid(row=1, column=1, sticky="w", padx=(5, 0))

        first_fit_space = ttk.Label(
            first_fit_frame, text="Remaining Space:", font=("Arial", 11, "bold")
        )
        first_fit_space.grid(row=2, column=0, sticky="w")
        first_fit_space_text = ttk.Label(
            first_fit_frame,
            text="If the allocated block is larger than the request, the remaining portion \n"
            "is left as a new free block.",
            style="Normal.TLabel",
        )
        first_fit_space_text.grid(
            row=2, column=1, sticky="w", padx=(5, 0), pady=(0, 10)
        )

        # 2. Next Fit
        next_fit_heading = ttk.Label(
            content_frame, text="2. Next Fit", style="Subheading.TLabel"
        )
        next_fit_heading.grid(row=5, column=0, sticky="w")

        next_fit_frame = ttk.Frame(content_frame)
        next_fit_frame.grid(row=6, column=0, sticky="w", padx=20)

        next_fit_process = ttk.Label(
            next_fit_frame, text="Process:", font=("Arial", 11, "bold")
        )
        next_fit_process.grid(row=0, column=0, sticky="w")
        next_fit_process_text = ttk.Label(
            next_fit_frame,
            text="Start searching from the location where the previous allocation search finished.",
            style="Normal.TLabel",
        )
        next_fit_process_text.grid(row=0, column=1, sticky="w", padx=(5, 0))

        next_fit_action = ttk.Label(
            next_fit_frame, text="Action:", font=("Arial", 11, "bold")
        )
        next_fit_action.grid(row=1, column=0, sticky="w")
        next_fit_action_text = ttk.Label(
            next_fit_frame,
            text="Allocate the requested memory from the first free block encountered from that \n"
            "point onwards that is equal to or larger than the requested size.",
            style="Normal.TLabel",
        )
        next_fit_action_text.grid(row=1, column=1, sticky="w", padx=(5, 0))

        next_fit_space = ttk.Label(
            next_fit_frame, text="Remaining Space:", font=("Arial", 11, "bold")
        )
        next_fit_space.grid(row=2, column=0, sticky="w")
        next_fit_space_text = ttk.Label(
            next_fit_frame,
            text="Similar to First Fit, the remaining space becomes a new free block.",
            style="Normal.TLabel",
        )
        next_fit_space_text.grid(row=2, column=1, sticky="w", padx=(5, 0))

        next_fit_benefit = ttk.Label(
            next_fit_frame, text="Benefit:", font=("Arial", 11, "bold")
        )
        next_fit_benefit.grid(row=3, column=0, sticky="w")
        next_fit_benefit_text = ttk.Label(
            next_fit_frame,
            text="It tends to distribute memory blocks more evenly throughout the memory.",
            style="Normal.TLabel",
        )
        next_fit_benefit_text.grid(
            row=3, column=1, sticky="w", padx=(5, 0), pady=(0, 10)
        )

        # 3. Best Fit
        best_fit_heading = ttk.Label(
            content_frame, text="3. Best Fit", style="Subheading.TLabel"
        )
        best_fit_heading.grid(row=7, column=0, sticky="w")

        best_fit_frame = ttk.Frame(content_frame)
        best_fit_frame.grid(row=8, column=0, sticky="w", padx=20)

        best_fit_process = ttk.Label(
            best_fit_frame, text="Process:", font=("Arial", 11, "bold")
        )
        best_fit_process.grid(row=0, column=0, sticky="w")
        best_fit_process_text = ttk.Label(
            best_fit_frame,
            text="Scan the entire list of free blocks.",
            style="Normal.TLabel",
        )
        best_fit_process_text.grid(row=0, column=1, sticky="w", padx=(5, 0))

        best_fit_action = ttk.Label(
            best_fit_frame, text="Action:", font=("Arial", 11, "bold")
        )
        best_fit_action.grid(row=1, column=0, sticky="w")
        best_fit_action_text = ttk.Label(
            best_fit_frame,
            text="Allocate the requested memory from the free block that is the smallest \n"
            "among all blocks that can satisfy the request.",
            style="Normal.TLabel",
        )
        best_fit_action_text.grid(row=1, column=1, sticky="w", padx=(5, 0))

        best_fit_space = ttk.Label(
            best_fit_frame, text="Remaining Space:", font=("Arial", 11, "bold")
        )
        best_fit_space.grid(row=2, column=0, sticky="w")
        best_fit_space_text = ttk.Label(
            best_fit_frame,
            text="The remaining space is left as a new free block.",
            style="Normal.TLabel",
        )
        best_fit_space_text.grid(row=2, column=1, sticky="w", padx=(5, 0))

        best_fit_goal = ttk.Label(
            best_fit_frame, text="Goal:", font=("Arial", 11, "bold")
        )
        best_fit_goal.grid(row=3, column=0, sticky="w")
        best_fit_goal_text = ttk.Label(
            best_fit_frame,
            text="To minimize the wasted space (internal fragmentation) within the allocated block.",
            style="Normal.TLabel",
        )
        best_fit_goal_text.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=(0, 10))

        # 4. Worst Fit
        worst_fit_heading = ttk.Label(
            content_frame, text="4. Worst Fit", style="Subheading.TLabel"
        )
        worst_fit_heading.grid(row=9, column=0, sticky="w")

        worst_fit_frame = ttk.Frame(content_frame)
        worst_fit_frame.grid(row=10, column=0, sticky="w", padx=20)

        worst_fit_process = ttk.Label(
            worst_fit_frame, text="Process:", font=("Arial", 11, "bold")
        )
        worst_fit_process.grid(row=0, column=0, sticky="w")
        worst_fit_process_text = ttk.Label(
            worst_fit_frame,
            text="Scan the entire list of free blocks.",
            style="Normal.TLabel",
        )
        worst_fit_process_text.grid(row=0, column=1, sticky="w", padx=(5, 0))

        worst_fit_action = ttk.Label(
            worst_fit_frame, text="Action:", font=("Arial", 11, "bold")
        )
        worst_fit_action.grid(row=1, column=0, sticky="w")
        worst_fit_action_text = ttk.Label(
            worst_fit_frame,
            text="Allocate the requested memory from the free block that is the largest \n"
            "among all blocks that can satisfy the request.",
            style="Normal.TLabel",
        )
        worst_fit_action_text.grid(row=1, column=1, sticky="w", padx=(5, 0))

        worst_fit_space = ttk.Label(
            worst_fit_frame, text="Remaining Space:", font=("Arial", 11, "bold")
        )
        worst_fit_space.grid(row=2, column=0, sticky="w")
        worst_fit_space_text = ttk.Label(
            worst_fit_frame,
            text="The remaining space is left as a new free block.",
            style="Normal.TLabel",
        )
        worst_fit_space_text.grid(row=2, column=1, sticky="w", padx=(5, 0))

        worst_fit_goal = ttk.Label(
            worst_fit_frame, text="Goal:", font=("Arial", 11, "bold")
        )
        worst_fit_goal.grid(row=3, column=0, sticky="w")
        worst_fit_goal_text = ttk.Label(
            worst_fit_frame,
            text="To leave the largest possible remaining free block, hoping it will be useful \n"
            "for future larger requests.",
            style="Normal.TLabel",
        )
        worst_fit_goal_text.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=(0, 10))

        # Justification for First Fit
        justification_heading = ttk.Label(
            content_frame, text="Justification for First Fit", style="Heading.TLabel"
        )
        justification_heading.grid(row=11, column=0, sticky="w")

        justification_text = (
            "While different algorithms have their merits, First Fit is often considered a practical and "
            "efficient choice for memory allocation due to several factors:"
        )
        justification_intro = ttk.Label(
            content_frame,
            text=justification_text,
            style="Normal.TLabel",
            wraplength=750,
        )
        justification_intro.grid(row=12, column=0, sticky="w", pady=(0, 10))

        # Memory Blocks and Sizes
        blocks_heading = ttk.Label(
            content_frame, text="Memory Blocks and Sizes", style="Subheading.TLabel"
        )
        blocks_heading.grid(row=13, column=0, sticky="w")

        blocks_example_text = (
            "Consider a scenario with the following memory blocks of varying sizes:"
        )
        blocks_example = ttk.Label(
            content_frame,
            text=blocks_example_text,
            style="Normal.TLabel",
            wraplength=750,
        )
        blocks_example.grid(row=14, column=0, sticky="w", padx=20)

        # Create a frame for memory blocks bullet points
        blocks_frame = ttk.Frame(content_frame)
        blocks_frame.grid(row=15, column=0, sticky="w", padx=40)

        blocks = [
            "Block 1: 100 KB",
            "Block 2: 500 KB",
            "Block 3: 200 KB",
            "Block 4: 300 KB",
            "Block 5: 600 KB",
        ]

        for i, block in enumerate(blocks):
            block_label = ttk.Label(
                blocks_frame, text="\u2022 " + block, style="Normal.TLabel"
            )
            block_label.grid(row=i, column=0, sticky="w")

        comparison_text = (
            "Let's say we have a request for 250 KB.\n\n"
            "First Fit: It would scan from Block 1. Block 1 (100 KB) is too small. Block 2 (500 KB) is large enough. "
            "First Fit allocates 250 KB from Block 2, leaving a 250 KB free block.\n\n"
            "Best Fit: It would scan all blocks. Block 2 (500 KB), Block 4 (300 KB), and Block 5 (600 KB) are large enough. "
            "Best Fit would choose Block 4 (300 KB) as it's the smallest sufficient block, allocating 250 KB and leaving a 50 KB free block.\n\n"
            "Worst Fit: It would choose Block 5 (600 KB) as it's the largest, allocating 250 KB and leaving a 350 KB free block.\n\n"
            "In this simple example, First Fit quickly finds a suitable block without scanning the entire memory, which can be faster."
        )
        comparison = ttk.Label(
            content_frame, text=comparison_text, style="Normal.TLabel", wraplength=750
        )
        comparison.grid(row=16, column=0, sticky="w", padx=20, pady=(5, 10))

        # Allocation and Deallocation Requests
        alloc_heading = ttk.Label(
            content_frame,
            text="Allocation and Deallocation Requests",
            style="Subheading.TLabel",
        )
        alloc_heading.grid(row=17, column=0, sticky="w")

        alloc_text = (
            "Simulating a series of allocation and deallocation requests highlights First Fit's efficiency. "
            "First Fit's speed comes from its straightforward approach: it stops searching as soon as a suitable "
            "block is found. This is particularly beneficial when the memory has many free blocks at the beginning. "
            "While Best Fit and Worst Fit need to scan more or all of the free list, First Fit's search time is, "
            "on average, less.\n\n"
            "Deallocation in First Fit is also relatively simple; the deallocated block is typically merged with "
            "adjacent free blocks if they exist."
        )
        alloc_label = ttk.Label(
            content_frame, text=alloc_text, style="Normal.TLabel", wraplength=750
        )
        alloc_label.grid(row=18, column=0, sticky="w", padx=20, pady=(0, 10))

        # Fragmentation
        frag_heading = ttk.Label(
            content_frame, text="Fragmentation", style="Subheading.TLabel"
        )
        frag_heading.grid(row=19, column=0, sticky="w")

        frag_text = "Fragmentation is a key issue in memory allocation."
        frag_intro = ttk.Label(
            content_frame, text=frag_text, style="Normal.TLabel", wraplength=750
        )
        frag_intro.grid(row=20, column=0, sticky="w", padx=20)

        internal_frag_label = ttk.Label(
            content_frame, text="Internal Fragmentation:", font=("Arial", 11, "bold")
        )
        internal_frag_label.grid(row=21, column=0, sticky="w", padx=40)
        internal_frag_text = (
            "Occurs when the allocated memory block is larger than the requested size, and the excess "
            "space within the block cannot be used by other processes. Best Fit aims to minimize this, "
            "but First Fit can also result in internal fragmentation when a larger block is used for a smaller request."
        )
        internal_frag = ttk.Label(
            content_frame,
            text=internal_frag_text,
            style="Normal.TLabel",
            wraplength=730,
        )
        internal_frag.grid(row=22, column=0, sticky="w", padx=40)

        external_frag_label = ttk.Label(
            content_frame, text="External Fragmentation:", font=("Arial", 11, "bold")
        )
        external_frag_label.grid(row=23, column=0, sticky="w", padx=40, pady=(10, 0))
        external_frag_text = (
            "Occurs when there is enough total free space to satisfy a request, but the free space is "
            "scattered in small, non-contiguous blocks. All simple contiguous allocation algorithms like "
            "First Fit, Best Fit, and Worst Fit are susceptible to external fragmentation over time."
        )
        external_frag = ttk.Label(
            content_frame,
            text=external_frag_text,
            style="Normal.TLabel",
            wraplength=730,
        )
        external_frag.grid(row=24, column=0, sticky="w", padx=40)

        frag_summary_text = (
            "First Fit's handling of fragmentation is a trade-off. While it might lead to more external "
            "fragmentation over time compared to Best Fit (as it tends to use up smaller blocks at the beginning, "
            "leaving larger blocks fragmented later), its speed often compensates for this in many practical "
            "scenarios. The tendency of First Fit to use blocks at the beginning can also lead to larger free "
            "blocks accumulating towards the end of memory, which can be beneficial for larger future requests."
        )
        frag_summary = ttk.Label(
            content_frame, text=frag_summary_text, style="Normal.TLabel", wraplength=750
        )
        frag_summary.grid(row=25, column=0, sticky="w", padx=20, pady=(10, 10))

        # Justification Summary
        summary_heading = ttk.Label(
            content_frame, text="Justification Summary", style="Subheading.TLabel"
        )
        summary_heading.grid(row=26, column=0, sticky="w")

        summary_text = (
            "First Fit is often preferred in practice due to its speed of allocation. It requires less overhead "
            "for searching compared to Best Fit and Worst Fit, which must scan more or all of the free list. "
            "While it may not be optimal in terms of minimizing internal fragmentation or preventing external "
            "fragmentation entirely, its simplicity and speed make it a good general-purpose algorithm, "
            'especially in systems where allocation speed is critical. The overhead of searching for the "best" '
            'or "worst" fit can outweigh the potential benefits in terms of fragmentation in many real-world scenarios.'
        )
        summary_label = ttk.Label(
            content_frame, text=summary_text, style="Normal.TLabel", wraplength=750
        )
        summary_label.grid(row=27, column=0, sticky="w", padx=20, pady=(0, 20))

        # Close button
        close_button = ttk.Button(
            content_frame, text="Close", command=info_window.destroy
        )
        close_button.grid(row=28, column=0, pady=10)

        # Update the scrollregion after the window size is updated
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Set the width of the canvas window to fill the available space
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        canvas.bind("<Configure>", configure_scroll_region)
        content_frame.bind("<Configure>", configure_scroll_region)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # Focus on the info window
            info_window.focus_set()
            info_window.grab_set()  # Make window modal

            # Wait for window to appear before configuring the scroll region
            info_window.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

    def show_about(e):
        messagebox.showinfo(
            "About",
            "OS OEL - Spring'25\nSubmitted By:\n• Abdul Rehman\n• Ahmed Javed\n• Capt. Haroon Ishaq",
        )


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryAllocatorApp(root)
    root.mainloop()

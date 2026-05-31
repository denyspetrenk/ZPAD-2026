import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons
import seaborn as sns
from scipy.signal import butter, filtfilt

sns.set_theme(style="whitegrid")

class InteractiveHarmonicApp:
    def __init__(self):
        # Початкові параметри
        self.init_amp = 1.0
        self.init_freq = 0.25
        self.init_phase = 0.0
        self.init_noise_mean = 0.0
        self.init_noise_cov = 0.1
        self.init_cutoff = 1.5
        self.show_noise = True
        
        self.t = np.linspace(0, 10, 1000)
        
        # Seeded noise
        self.current_noise_mean = self.init_noise_mean
        self.current_noise_cov = self.init_noise_cov
        self.noise = self.generate_noise(self.current_noise_mean, self.current_noise_cov)

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.fig.canvas.manager.set_window_title("Інтерактивний аналіз гармонік")
        
        plt.subplots_adjust(bottom=0.45) 
        
        y_clean = self.get_clean_harmonic(self.init_amp, self.init_freq, self.init_phase)
        y_noisy = y_clean + self.noise
        y_filtered = self.apply_filter(y_noisy, self.init_cutoff)

        self.line_noisy, = self.ax.plot(self.t, y_noisy, color='orange', alpha=0.7, label='Зашумлена (Noisy)')
        self.line_clean, = self.ax.plot(self.t, y_clean, color='blue', linestyle='--', linewidth=2, label='Чиста (Clean)')
        self.line_filtered, = self.ax.plot(self.t, y_filtered, color='purple', linewidth=2, label='Відфільтрована (Filtered)')
        
        self.ax.set_title("Гармоніка з шумом та фільтрацією")
        self.ax.set_xlabel("Час (t)")
        self.ax.set_ylabel("Амплітуда (y)")
        self.ax.set_ylim(-3, 3)
        self.ax.legend(loc='upper right')

        # Sliders
        axcolor = 'lightgoldenrodyellow'
        
        ax_amp = plt.axes([0.15, 0.35, 0.65, 0.03], facecolor=axcolor)
        ax_freq = plt.axes([0.15, 0.30, 0.65, 0.03], facecolor=axcolor)
        ax_phase = plt.axes([0.15, 0.25, 0.65, 0.03], facecolor=axcolor)
        ax_noise_m = plt.axes([0.15, 0.20, 0.65, 0.03], facecolor=axcolor)
        ax_noise_c = plt.axes([0.15, 0.15, 0.65, 0.03], facecolor=axcolor)
        ax_cutoff = plt.axes([0.15, 0.10, 0.65, 0.03], facecolor=axcolor)

        self.slider_amp = Slider(ax_amp, 'Амплітуда', 0.1, 2.0, valinit=self.init_amp)
        self.slider_freq = Slider(ax_freq, 'Частота', 0.01, 2.0, valinit=self.init_freq)
        self.slider_phase = Slider(ax_phase, 'Фаза', 0, 2*np.pi, valinit=self.init_phase)
        self.slider_noise_m = Slider(ax_noise_m, 'Шум (Середнє)', -1.0, 1.0, valinit=self.init_noise_mean)
        self.slider_noise_c = Slider(ax_noise_c, 'Шум (Дисперсія)', 0.0, 1.0, valinit=self.init_noise_cov)
        self.slider_cutoff = Slider(ax_cutoff, 'Зріз фільтра', 0.1, 5.0, valinit=self.init_cutoff)

        # Reset
        ax_reset = plt.axes([0.15, 0.025, 0.1, 0.04])
        self.button_reset = Button(ax_reset, 'Reset', color=axcolor, hovercolor='0.975')

        # Show Noise
        ax_check = plt.axes([0.8, 0.025, 0.15, 0.04])
        self.check_noise = CheckButtons(ax_check, ['Показати шум'], [self.show_noise])

        self.slider_amp.on_changed(self.update)
        self.slider_freq.on_changed(self.update)
        self.slider_phase.on_changed(self.update)
        self.slider_noise_m.on_changed(self.update)
        self.slider_noise_c.on_changed(self.update)
        self.slider_cutoff.on_changed(self.update)
        self.button_reset.on_clicked(self.reset)
        self.check_noise.on_clicked(self.toggle_noise)

    # ЛОГІКА
    def get_clean_harmonic(self, amp, freq, phase):
        """y(t) = A*sin(2*pi*f*t + phase)"""
        return amp * np.sin(2 * np.pi * freq * self.t + phase)

    def generate_noise(self, mean, cov):
        """Масив шуму на основі середнього та дисперсії (коваріації)"""
        std_dev = np.sqrt(cov) if cov > 0 else 0 
        return np.random.normal(mean, std_dev, len(self.t))

    def apply_filter(self, data, cutoff_freq):
        """Low-pass фільтр Баттерворта"""
        nyquist = 0.5 * (1.0 / (self.t[1] - self.t[0]))
        normal_cutoff = cutoff_freq / nyquist
        
        if normal_cutoff >= 1.0:
            normal_cutoff = 0.99
            
        b, a = butter(4, normal_cutoff, btype='low', analog=False)

        y_filtered = filtfilt(b, a, data)
        return y_filtered

    def update(self, val):
        amp = self.slider_amp.val
        freq = self.slider_freq.val
        phase = self.slider_phase.val
        n_mean = self.slider_noise_m.val
        n_cov = self.slider_noise_c.val
        cutoff = self.slider_cutoff.val

        if n_mean != self.current_noise_mean or n_cov != self.current_noise_cov:
            self.noise = self.generate_noise(n_mean, n_cov)
            self.current_noise_mean = n_mean
            self.current_noise_cov = n_cov

        y_clean = self.get_clean_harmonic(amp, freq, phase)
        y_noisy = y_clean + self.noise
        y_filtered = self.apply_filter(y_noisy, cutoff)

        self.line_clean.set_ydata(y_clean)
        self.line_noisy.set_ydata(y_noisy)
        self.line_filtered.set_ydata(y_filtered)

        self.fig.canvas.draw_idle()

    def reset(self, event):
        self.slider_amp.reset()
        self.slider_freq.reset()
        self.slider_phase.reset()
        self.slider_noise_m.reset()
        self.slider_noise_c.reset()
        self.slider_cutoff.reset()

    def toggle_noise(self, label):
        self.show_noise = not self.show_noise
        self.line_noisy.set_visible(self.show_noise)
        self.fig.canvas.draw_idle()


if __name__ == '__main__':
    print("Інструкція:")
    print("1. Змінюйте параметри гармоніки (Амплітуда, Частота, Фаза).")
    print("2. Регулюйте рівень шуму. Шум генерується наново ТІЛЬКИ при зміні його параметрів.")
    print("3. Налаштуйте 'Зріз фільтра' для згладжування (менше значення = сильніше згладжування).")
    print("4. Використовуйте чекбокс 'Показати шум', щоб приховати помаранчеву лінію.")
    
    app = InteractiveHarmonicApp()
    plt.show()
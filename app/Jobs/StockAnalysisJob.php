<?php

namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Throwable;

class StockAnalysisJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    protected $parameters;

    /**
     * Job timeout w sekundach (10 minut)
     */
    public $timeout = 600;

    /**
     * Create a new job instance.
     */
    public function __construct(array $parameters)
    {
        $this->parameters = $parameters;
    }

    /**
     * Execute the job.
     */
    public function handle(): void
    {
        try {
            Log::info('Rozpoczęcie analizy giełdowej', $this->parameters);

            $command = [
                'docker', 'exec', 'stock-python',
                'python', '/app/stock_model.py',
                '--ticker', $this->parameters['ticker'],
                '--start_date', $this->parameters['start_date'],
                '--test_size_pct', (string)$this->parameters['test_size_pct'],
                '--forecast_days', (string)$this->parameters['forecast_days']
            ];

            $process = new Process($command);
            $process->setTimeout($this->timeout);
            $process->run();

            if (!$process->isSuccessful()) {
                throw new ProcessFailedException($process);
            }

            Log::info('Analiza giełdowa zakończona pomyślnie', [
                'ticker' => $this->parameters['ticker'],
                'output' => $process->getOutput()
            ]);

        } catch (\Exception $e) {
            Log::error('Błąd podczas analizy giełdowej', [
                'parameters' => $this->parameters,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            throw $e; // Re-throw aby job został oznaczony jako failed
        }
    }

    /**
     * Handle a job failure.
     */
    public function failed(\Exception $exception)
    {
        Log::error('Job analizy giełdowej nieudany', [
            'parameters' => $this->parameters,
            'error' => $exception->getMessage()
        ]);

        // Tutaj możesz dodać dodatkową logikę, np.:
        // - Wysłanie notyfikacji do administratora
        // - Zapisanie błędu w bazie danych
        // - Wysłanie emaila do użytkownika
    }
}

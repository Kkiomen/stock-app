<?php

use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('welcome');
})->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('dashboard', function () {
        return Inertia::render('dashboard');
    })->name('dashboard');

    Route::get('markets', [\App\Http\Controllers\MarketController::class, 'index'])->name('markets');
    Route::get('markets/{stock}', [\App\Http\Controllers\MarketController::class, 'details'])->name('markets_details');
});

require __DIR__.'/settings.php';
require __DIR__.'/auth.php';

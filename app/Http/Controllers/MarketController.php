<?php

namespace App\Http\Controllers;

use App\Models\Stock;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class MarketController extends Controller
{
    /**
     * Show the user's profile settings page.
     */
    public function index(Request $request): Response
    {
        $stocks = Stock::all();
        return Inertia::render('markets/page', [
            'stocks' => $stocks,
        ]);
    }
}
